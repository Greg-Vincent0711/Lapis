#!/usr/bin/env bash
# Deploys the Lapis backend (API Lambdas + the Discord bot on EC2) through CloudFormation.
#
#   ./deploy.sh            test, build, upload, preview the changes, ask, then apply
#   ./deploy.sh --preview  stop after showing what would change
#   ./deploy.sh --yes      apply without asking (still refuses anything that would delete data)
#
# Optional overrides (otherwise the stack keeps its current value, or the template default):
#   SITE_ORIGINS="http://localhost:5173,https://lapis.example.com"
#   DISCORD_REDIRECT_URI="https://lapis.example.com/auth/callback"
# The Discord client secret is read from CLIENT_SECRET in .env (or DISCORD_CLIENT_SECRET),
# and the bot token from TOKEN in .env (or DISCORD_BOT_TOKEN).
set -euo pipefail

STACK=LapisBackend
TEMPLATE=src/lapis/FormationTemplate.YAML
REGION=${AWS_REGION:-us-east-1}
BUCKET="lapis-memory-$(aws sts get-caller-identity --query Account --output text)"
PREVIEW=false; ASSUME_YES=false
for arg in "$@"; do
  case "$arg" in
    --preview) PREVIEW=true ;;
    --yes) ASSUME_YES=true ;;
    *) echo "Unknown option: $arg"; exit 2 ;;
  esac
done
cd "$(dirname "$0")"

step() { printf '\n==> %s\n' "$*"; }

step "Running the tests"
python3 -m pytest -q src/lapis/tests

step "Checking the seed tools binary"
# Lambda runs on Linux ARM; a Mac build here would fail only at runtime
if ! file src/lapis/inputHandler | grep -q "ARM aarch64.*GNU/Linux"; then
  echo "src/lapis/inputHandler must be a Linux ARM (aarch64) build. Found: $(file -b src/lapis/inputHandler 2>&1)"
  exit 1
fi

step "Building the Lambda zips"
BUILD=$(mktemp -d)
trap 'rm -rf "$BUILD"' EXIT
COMMON_EXCLUDES=("src/lapis/lapis.py" "src/lapis/tests/*" "src/SeedInfoFns/*" "*.YAML" "*__pycache__*" "*.DS_Store")
zip -qr "$BUILD/db.zip" src -x "${COMMON_EXCLUDES[@]}" "src/lapis/inputHandler"
zip -qr "$BUILD/seed.zip" src -x "${COMMON_EXCLUDES[@]}" "src/lapis/api/db_lambda.py" "src/lapis/api/cache.py" \
  "src/lapis/helpers/docstrings.py" "src/lapis/helpers/embed.py" "src/lapis/helpers/paginator.py"
# the bot needs everything the API has plus lapis.py, the seed binary and its pip requirements
zip -qr "$BUILD/bot.zip" src requirements.txt -x "src/lapis/tests/*" "src/SeedInfoFns/*" "*.YAML" "*__pycache__*" "*.DS_Store"

# a unique name per build is what makes CloudFormation notice the code changed
VERSION="$(git rev-parse --short HEAD)$(git diff --quiet HEAD -- src || echo "-dirty")-$(date +%Y%m%d%H%M%S)"
DB_KEY="lambda/DB_lambda-$VERSION.zip"
SEED_KEY="lambda/seed_lambda-$VERSION.zip"

step "Uploading code to s3://$BUCKET/lambda/ ($VERSION)"
aws s3 cp --quiet "$BUILD/db.zip" "s3://$BUCKET/$DB_KEY"
aws s3 cp --quiet "$BUILD/seed.zip" "s3://$BUCKET/$SEED_KEY"

step "Preparing parameters"
if [[ -z "${DISCORD_CLIENT_SECRET:-}" && -f .env ]]; then
  # python-dotenv (what the bot uses) handles spaces around "=", quotes and comments
  DISCORD_CLIENT_SECRET=$(python3 -c "from dotenv import dotenv_values; print(dotenv_values('.env').get('CLIENT_SECRET') or '')")
fi
if [[ -z "${DISCORD_BOT_TOKEN:-}" && -f .env ]]; then
  DISCORD_BOT_TOKEN=$(python3 -c "from dotenv import dotenv_values; print(dotenv_values('.env').get('TOKEN') or '')")
fi
EXISTING=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query 'Stacks[0].Parameters[].ParameterKey' --output text 2>/dev/null || true)
# parameters go through a private temp file so the secret never appears in the process list
PARAMS="$BUILD/params.json"
DB_KEY="$DB_KEY" SEED_KEY="$SEED_KEY" EXISTING="$EXISTING" \
SECRET="${DISCORD_CLIENT_SECRET:-}" BOT_TOKEN="${DISCORD_BOT_TOKEN:-}" ORIGINS="${SITE_ORIGINS:-}" REDIRECT="${DISCORD_REDIRECT_URI:-}" \
python3 - > "$PARAMS" <<'PY'
import json, os
existing = set(os.environ["EXISTING"].split())
params = [
    {"ParameterKey": "DBCodeKey", "ParameterValue": os.environ["DB_KEY"]},
    {"ParameterKey": "SeedCodeKey", "ParameterValue": os.environ["SEED_KEY"]},
]
def keep_or_set(key, value):
    if value:
        params.append({"ParameterKey": key, "ParameterValue": value})
    elif key in existing:
        # leaving it out would reset it to the template default
        params.append({"ParameterKey": key, "UsePreviousValue": True})
keep_or_set("DiscordClientSecret", os.environ["SECRET"])
keep_or_set("SiteOrigins", os.environ["ORIGINS"])
keep_or_set("DiscordRedirectUri", os.environ["REDIRECT"])
keep_or_set("DiscordBotToken", os.environ["BOT_TOKEN"])
if not any(p["ParameterKey"] == "DiscordClientSecret" for p in params):
    raise SystemExit("No Discord client secret: set CLIENT_SECRET in .env or DISCORD_CLIENT_SECRET.")
if not any(p["ParameterKey"] == "DiscordBotToken" for p in params):
    raise SystemExit("No Discord bot token: set TOKEN in .env or DISCORD_BOT_TOKEN.")
print(json.dumps(params))
PY
chmod 600 "$PARAMS"

step "Creating a change set (nothing changes yet)"
CHANGE_SET="deploy-$VERSION"
aws cloudformation create-change-set --stack-name "$STACK" --region "$REGION" \
  --change-set-name "$CHANGE_SET" --template-body "file://$TEMPLATE" \
  --parameters "file://$PARAMS" --capabilities CAPABILITY_NAMED_IAM >/dev/null
if ! aws cloudformation wait change-set-create-complete --stack-name "$STACK" --region "$REGION" --change-set-name "$CHANGE_SET" 2>/dev/null; then
  REASON=$(aws cloudformation describe-change-set --stack-name "$STACK" --region "$REGION" --change-set-name "$CHANGE_SET" --query StatusReason --output text)
  aws cloudformation delete-change-set --stack-name "$STACK" --region "$REGION" --change-set-name "$CHANGE_SET"
  if [[ "$REASON" == *"didn't contain changes"* || "$REASON" == *"No updates"* ]]; then
    echo "Nothing to deploy."; exit 0
  fi
  echo "Change set failed: $REASON"; exit 1
fi

step "Planned changes"
CHANGES=$(aws cloudformation describe-change-set --stack-name "$STACK" --region "$REGION" --change-set-name "$CHANGE_SET" \
  --query 'Changes[].ResourceChange.[Action,LogicalResourceId,ResourceType,Replacement]' --output text)
printf '%-8s %-28s %-32s %s\n' ACTION RESOURCE TYPE REPLACE
echo "$CHANGES" | awk '{printf "%-8s %-28s %-32s %s\n", $1, $2, $3, $4}'

# the table holds every user's data and the bucket every image: never let a deploy remove or replace them
if echo "$CHANGES" | awk '($2=="LapisTable" || $2=="LapisCodeAndImages") && ($1=="Remove" || $4=="True")' | grep -q .; then
  echo; echo "REFUSING: this would remove or replace the data table or the bucket."
  aws cloudformation delete-change-set --stack-name "$STACK" --region "$REGION" --change-set-name "$CHANGE_SET"
  exit 1
fi

if $PREVIEW; then
  aws cloudformation delete-change-set --stack-name "$STACK" --region "$REGION" --change-set-name "$CHANGE_SET"
  echo; echo "Preview only; nothing was changed."; exit 0
fi
if ! $ASSUME_YES; then
  read -r -p $'\nApply these changes? [y/N] ' answer
  if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    aws cloudformation delete-change-set --stack-name "$STACK" --region "$REGION" --change-set-name "$CHANGE_SET"
    echo "Cancelled; nothing was changed."; exit 0
  fi
fi

# uploaded only once the change is approved: a new instance pulls this while it boots, and an
# existing one would pick it up on its next restart
step "Uploading the bot code to s3://$BUCKET/bot/"
aws s3 cp --quiet "$BUILD/bot.zip" "s3://$BUCKET/bot/lapis-bot.zip"

step "Applying (1-3 minutes; up to 10 when the bot's instance is created or replaced)"
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
aws cloudformation execute-change-set --stack-name "$STACK" --region "$REGION" --change-set-name "$CHANGE_SET"
if ! aws cloudformation wait stack-update-complete --stack-name "$STACK" --region "$REGION" 2>/dev/null; then
  echo "The update failed and CloudFormation rolled it back; nothing changed. What failed:"
  # only this run's events, and not the "cancelled" ones that follow any real failure
  aws cloudformation describe-stack-events --stack-name "$STACK" --region "$REGION" \
    --query "StackEvents[?Timestamp>='$STARTED' && contains(ResourceStatus, 'FAILED') && !contains(ResourceStatusReason, 'cancelled')].[LogicalResourceId,ResourceStatusReason]" \
    --output text
  exit 1
fi

step "Checking the live API"
API_URL=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$API_URL/locations")
if [[ "$STATUS" == "401" ]]; then
  echo "OK: $API_URL is up and rejects requests without a token."
else
  echo "Unexpected: GET $API_URL/locations without a token returned $STATUS (expected 401)."; exit 1
fi

step "Updating the bot on EC2"
INSTANCE_ID=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='BotInstanceId'].OutputValue" --output text)
# the SSM agent can take a minute to check in after the instance is created
for _ in $(seq 1 18); do
  PING=$(aws ssm describe-instance-information --region "$REGION" \
    --filters "Key=InstanceIds,Values=$INSTANCE_ID" --query 'InstanceInformationList[0].PingStatus' --output text)
  [[ "$PING" == "Online" ]] && break
  sleep 10
done
if [[ "$PING" != "Online" ]]; then
  echo "The bot's instance ($INSTANCE_ID) isn't reachable through Systems Manager; the bot code wasn't refreshed."; exit 1
fi
# a brand-new instance already pulled this code while booting; running it again is harmless
COMMAND_ID=$(aws ssm send-command --region "$REGION" --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript --comment "Lapis $VERSION" \
  --parameters 'commands=["/opt/lapis/update.sh"]' --query Command.CommandId --output text)
aws ssm wait command-executed --region "$REGION" --command-id "$COMMAND_ID" --instance-id "$INSTANCE_ID" 2>/dev/null || true
RESULT=$(aws ssm get-command-invocation --region "$REGION" --command-id "$COMMAND_ID" --instance-id "$INSTANCE_ID" \
  --query '[Status,StandardOutputContent,StandardErrorContent]' --output text)
if [[ "$RESULT" != Success* ]]; then
  echo "Updating the bot failed:"; echo "$RESULT"; exit 1
fi
echo "OK: the bot on $INSTANCE_ID is running $VERSION."

echo; echo "Deployed $VERSION. Website setting: VITE_APP_API_ENDPOINT=$API_URL"

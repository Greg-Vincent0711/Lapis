# Lapis

A Minecraft bot built around AWS Microservices and Minecraft-based tooling (lookup Cubitect and the Cubiomes Library).

Lapis has an [entire website](https://github.com/Greg-Vincent0711/Lapis-Site) (currently in the works) dedicated to its inner workings and all the stats for fellow nerds. It also has the user's stored servi
ces. But generally, Lapis is meant to resolve a couple small annoyances I had while enduring my annual two week Minecraft phase. Namely, having a consistent place to store coordinates that wasn't my camera roll, only to then have to manually delete a bunch of screenshots later.

You can think of Lapis as the younger, more complex sibling to [this](https://github.com/Greg-Vincent0711/Multi-purpose-Bot-for-Python/blob/main/DIscordBotVer%231.py) earlier project I made with a friend.

## Building the C Code

If someone wants to use the C code I wrote together with Cubiomes:

To use the lib and compile programs:
1. `cd` into `external/cubiomes`
2. Run `make`
3. `cd ../../src/SeedInfoFns`
4. Run `make`

## Deploying the backend

All AWS resources are defined in [src/lapis/FormationTemplate.YAML](src/lapis/FormationTemplate.YAML) (stack `LapisBackend`, us-east-1). From the repo root:

```bash
./deploy.sh --preview   # run the tests, build and upload the code, show what would change; changes nothing
./deploy.sh             # same, then asks before applying
```

The script reads the Discord client secret from `CLIENT_SECRET` in `.env`, and refuses any change that would delete or replace the DynamoDB table or the S3 bucket. `src/lapis/inputHandler` must be the Linux ARM build that Lambda runs. When the website is hosted, add its domain:

```bash
SITE_ORIGINS="http://localhost:5173,https://<site>" DISCORD_REDIRECT_URI="https://<site>/auth/callback" ./deploy.sh
```

The Fernet encryption key, the Cognito user pool and the Python dependencies layer are deliberately kept outside the stack and passed in as parameters, so no stack change can delete them.

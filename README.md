# Lapis

A Minecraft bot built around AWS Microservices that extends [Minecraft-based tooling](https://github.com/Cubitect/cubiomes).

Lapis has an [entire website](https://main.d15e4j6jt7lh3i.amplifyapp.com/) explaining my thought process creating this project and it's inner workings. Users can sign into this site(thanks to AWS Cognito) and store/retrieve locations and images of their own MC world. 

[Add Lapis to your Discord Server Here!]([https://discord.com/oauth2/authorize?client_id=1342331009336868915](https://discord.com/oauth2/authorize?client_id=1342331009336868915&permissions=379904&integration_type=0&scope=bot))


https://github.com/user-attachments/assets/957de5e1-8075-457c-a2e5-3137d739d500





You can think of Lapis as the younger, more complex sibling to [this](https://github.com/Greg-Vincent0711/Multi-purpose-Bot-for-Python/blob/main/DIscordBotVer%231.py) earlier project I made with a friend in 2021.

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

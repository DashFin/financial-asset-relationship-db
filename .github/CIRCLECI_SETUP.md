# CircleCI Setup Guide

## SSH Authentication Issue

If you encounter the following error during CircleCI builds:

```
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

This indicates that CircleCI doesn't have proper SSH access to the repository.

## Solution

### Option 1: Add User Key (Recommended)

1. Go to your CircleCI project settings
2. Navigate to **SSH Keys** section
3. Click **Add User Key**
4. Authorize CircleCI to access your GitHub account
5. CircleCI will automatically add the necessary SSH key

### Option 2: Add Deploy Key

1. Generate an SSH key pair locally
2. Add the public key to GitHub repository settings under **Deploy Keys**
3. Add the private key to CircleCI project settings under **SSH Keys**

## Documentation

For more details, see: https://circleci.com/docs/github-integration/#deploy-keys-and-user-keys

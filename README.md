# Jenkins Black Formatter Pipeline — Complete Beginner-to-Professional Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Git Repository Structure](#git-repository-structure)
4. [Prerequisites — What You Need Before Starting](#prerequisites--what-you-need-before-starting)
5. [Part 1: Set Up Your Local Machine (Jenkins Master)](#part-1-set-up-your-local-machine-jenkins-master)
6. [Part 2: Install Jenkins on Ubuntu](#part-2-install-jenkins-on-ubuntu)
7. [Part 3: Initial Jenkins Configuration (Web UI)](#part-3-initial-jenkins-configuration-web-ui)
8. [Part 4: Install Required Jenkins Plugins](#part-4-install-required-jenkins-plugins)
9. [Part 5: Set Up AWS Credentials in Jenkins](#part-5-set-up-aws-credentials-in-jenkins)
10. [Part 6: Set Up an EC2 as Jenkins Agent (Worker Node)](#part-6-set-up-an-ec2-as-jenkins-agent-worker-node)
11. [Part 7: Connect the Agent Node in Jenkins](#part-7-connect-the-agent-node-in-jenkins)
12. [Part 8: Set Up the S3 Bucket for Log Storage](#part-8-set-up-the-s3-bucket-for-log-storage)
13. [Part 9: Set Up GitHub Credentials](#part-9-set-up-github-credentials)
14. [Part 10: Create the Git Repository](#part-10-create-the-git-repository)
15. [Part 11: Understand the Jenkinsfile](#part-11-understand-the-jenkinsfile)
16. [Part 12: Create the Multibranch Pipeline in Jenkins](#part-12-create-the-multibranch-pipeline-in-jenkins)
17. [Part 13: Configure GitHub Webhooks for PR Triggers](#part-13-configure-github-webhooks-for-pr-triggers)
18. [Part 14: Test the Pipeline](#part-14-test-the-pipeline)
19. [Part 15: Common Commands Reference](#part-15-common-commands-reference)
20. [Part 16: Troubleshooting](#part-16-troubleshooting)

---

## Overview

**What we are building:**

A Jenkins CI/CD pipeline that automatically:
- Runs **`black`** (Python code formatter) on **all Python files** in your repository
- Triggers on **Pull Request (PR) level** — every time someone opens or updates a PR
- Also runs on a **30-minute schedule** to catch any issues
- Uses an **EC2 instance** as the Jenkins agent (worker) that actually runs the job
- Stores all build **logs in an S3 bucket**

**What is Black?**
`black` is a Python code formatter. It reformats your Python code to follow a consistent style. When used with `--check`, it only CHECKS if the code is formatted — it doesn't change anything.

**What is Jenkins?**
Jenkins is an open-source automation server. It helps automate building, testing, and deploying software. It uses "pipelines" defined in a `Jenkinsfile`.

**What is a Pipeline?**
A pipeline is a set of automated steps (stages) that Jenkins runs. For example: checkout code → install dependencies → run formatter → upload logs.

**What is an Agent/Node?**
A Jenkins agent (also called a node or worker) is a separate machine that runs the actual jobs. The Jenkins master assigns work to agents. We use a separate EC2 instance as our agent.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GitHub Repository                           │
│  (Contains: Jenkinsfile, Python source code, requirements.txt)      │
│                                                                     │
│  On PR open/update ──► Webhook triggers Jenkins                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                Local Machine (Laptop) — Jenkins Master               │
│                                                                      │
│  • Runs Jenkins server (port 8080)                                   │
│  • Manages pipelines, credentials, scheduling                        │
│  • Assigns jobs to agent nodes                                       │
│  • URL: http://localhost:8080                                        │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ SSH connection
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    EC2 Instance #2 — Jenkins Agent                   │
│                                                                      │
│  • Runs the actual pipeline jobs                                     │
│  • Has Python 3, pip, black installed                                │
│  • Has AWS CLI installed (for S3 uploads)                            │
│  • Label: "python-agent"                                             │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         AWS S3 Bucket                                │
│                                                                      │
│  • Stores build logs from each pipeline run                          │
│  • Path: s3://jenkins-black-logs-<account-id>/logs/                  │
│  • Each log file: logs/<job-name>/<build-number>/black-report.log    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Git Repository Structure

```
jenkins-black-formatter/
├── README.md                  ← This file — complete setup guide
├── Jenkinsfile                ← Pipeline definition (Jenkins reads this)
├── requirements.txt           ← Python dependencies (black)
├── setup.cfg                  ← Black configuration
├── .gitignore                 ← Files Git should ignore
├── scripts/
│   └── upload-logs-to-s3.sh   ← Script to upload logs to S3
├── src/
│   ├── __init__.py            ← Makes src a Python package
│   ├── app.py                 ← Sample Python application
│   └── utils.py               ← Sample utility functions
└── tests/
    ├── __init__.py            ← Makes tests a Python package
    └── test_app.py            ← Sample test file
```

**What is each file?**

| File | Purpose |
|------|---------|
| `Jenkinsfile` | Tells Jenkins WHAT to do — defines pipeline stages (checkout, install, format check, upload logs) |
| `requirements.txt` | Lists Python packages to install. Here it's just `black` |
| `setup.cfg` | Configuration for black (line length, which files to include/exclude) |
| `.gitignore` | Tells Git which files NOT to track (e.g., `__pycache__/`, `.venv/`) |
| `scripts/upload-logs-to-s3.sh` | Shell script that copies the log file to your S3 bucket |
| `src/*.py` | Sample Python source code that `black` will check |
| `tests/*.py` | Sample Python test code that `black` will also check |

---

## Prerequisites — What You Need Before Starting

Before starting, make sure you have:

| # | Item | Why You Need It | How to Get It |
|---|------|-----------------|---------------|
| 1 | **AWS Account** | To create EC2 agent instance and S3 bucket | https://aws.amazon.com/free |
| 2 | **AWS Access Key ID & Secret Access Key** | For Jenkins to upload to S3 | AWS Console → IAM → Users → Create Access Key |
| 3 | **GitHub Account** | To host your code repository | https://github.com/signup |
| 4 | **GitHub Personal Access Token (PAT)** | For Jenkins to read your repo & PR info | GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens |
| 5 | **SSH Key Pair** | To SSH into the agent EC2 and for Jenkins agent connection | Created when launching EC2 |
| 6 | **A computer with a browser** | To access Jenkins Web UI and AWS Console | You already have this! |

### AWS Credentials You'll Need (Write These Down!)

```
1. AWS Access Key ID:          AKIA________________
2. AWS Secret Access Key:      ________________________________________
3. AWS Region:                 e.g., us-east-1
4. EC2 Key Pair (.pem file):   Downloaded when creating agent EC2
5. GitHub PAT Token:           ghp_____________________________
6. Jenkins Admin Password:     (generated during install)
```

---

## Part 1: Set Up Your Local Machine (Jenkins Master)

### Step 1.1 — Ensure your laptop meets the requirements

Make sure your local machine has:

| Requirement | Minimum |
|-------------|---------|
| **OS** | Ubuntu/Debian Linux (or WSL2 on Windows) |
| **RAM** | At least 4 GB available |
| **Disk** | At least 10 GB free |
| **Network** | Internet access to download packages |

### Step 1.2 — Ensure required ports are available

Jenkins uses port **8080** for the web UI and port **50000** for agent communication. Make sure these ports are not already in use:

```bash
# Check if ports are free
sudo lsof -i :8080
sudo lsof -i :50000
```

If nothing is returned, the ports are available.

---

## Part 2: Install Jenkins on Ubuntu

> Run ALL these commands on your local machine (Jenkins Master).

### Step 2.1 — Update the system

```bash
# Update package list and upgrade all packages
sudo apt update && sudo apt upgrade -y
```

**What this does:** Downloads the latest list of available packages and upgrades all currently installed packages to their latest versions.

### Step 2.2 — Install Java (Jenkins requires Java)

```bash
# Install Java 17 (Long Term Support version)
sudo apt install -y fontconfig openjdk-17-jre
```

**What this does:** Jenkins is written in Java, so it needs the Java Runtime Environment (JRE) to run.

```bash
# Verify Java is installed
java -version
# Expected output: openjdk version "17.x.x"
```

### Step 2.3 — Add Jenkins repository and install

```bash
# Step 1: Download Jenkins GPG key (verifies package authenticity)
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key

# Step 2: Add Jenkins apt repository
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc]" \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# Step 3: Update package list again (now includes Jenkins)
sudo apt update

# Step 4: Install Jenkins
sudo apt install -y jenkins
```

**What this does:**
- Downloads a GPG key to verify that the Jenkins package is legitimate
- Adds the Jenkins package repository to your system
- Installs Jenkins from that repository

### Step 2.4 — Start and enable Jenkins

```bash
# Start Jenkins service
sudo systemctl start jenkins

# Enable Jenkins to start automatically on boot
sudo systemctl enable jenkins

# Check Jenkins status (should say "active (running)")
sudo systemctl status jenkins
```

**What each command does:**
- `start` → Starts Jenkins right now
- `enable` → Makes Jenkins start automatically when the server reboots
- `status` → Shows if Jenkins is running

### Step 2.5 — Get the initial admin password

```bash
# Display the initial admin password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

**Copy this password!** You'll need it in the next step. It looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### Step 2.6 — Open Jenkins in your browser

```
http://localhost:8080
```

Since Jenkins Master runs on your local machine, simply open `http://localhost:8080` in your browser.

---

## Part 3: Initial Jenkins Configuration (Web UI)

### Step 3.1 — Unlock Jenkins

1. Paste the initial admin password you copied earlier
2. Click **"Continue"**

### Step 3.2 — Install plugins

1. Click **"Install suggested plugins"**
2. Wait for installation to complete (takes 2-5 minutes)

### Step 3.3 — Create the first admin user

| Field | What to enter |
|-------|---------------|
| Username | `admin` (or whatever you prefer) |
| Password | A strong password (save this!) |
| Full name | Your name |
| Email | Your email |

3. Click **"Save and Continue"**

### Step 3.4 — Configure Jenkins URL

1. Confirm the URL: `http://localhost:8080/`
2. Click **"Save and Finish"**
3. Click **"Start using Jenkins"**

---

## Part 4: Install Required Jenkins Plugins

### Step 4.1 — Navigate to Plugin Manager

1. Go to **Dashboard** → **Manage Jenkins** → **Plugins** → **Available plugins**

### Step 4.2 — Search and install these plugins

Search for each one, check the box, then click **"Install"**:

| Plugin | Why We Need It |
|--------|---------------|
| **Pipeline** | Enables Jenkinsfile-based pipelines (likely already installed) |
| **Git** | Allows Jenkins to clone Git repositories (likely already installed) |
| **GitHub** | GitHub integration for webhooks and PR status |
| **GitHub Branch Source** | Enables Multibranch Pipeline with GitHub (auto-discovers PRs) |
| **Pipeline: Stage View** | Visual display of pipeline stages |
| **Amazon EC2** | Manages EC2 instances as Jenkins agents |
| **S3 publisher** | Publishes artifacts/logs to S3 |
| **Credentials Binding** | Securely injects credentials into pipeline |
| **SSH Agent** | Allows SSH connections to agent nodes |
| **Timestamper** | Adds timestamps to console output |

2. After checking all, click **"Install without restart"**
3. Check **"Restart Jenkins when installation is complete"** at the bottom

---

## Part 5: Set Up AWS Credentials in Jenkins

### Step 5.1 — Create an IAM User in AWS (if you haven't already)

1. Go to **AWS Console** → **IAM** → **Users** → **Create user**
2. User name: `jenkins-s3-user`
3. Click **Next**
4. **Attach policies directly** → Search and attach:
   - `AmazonS3FullAccess` (for S3 log uploads)
   - `AmazonEC2FullAccess` (for EC2 agent management)
5. Click **Create user**
6. Go to the user → **Security credentials** tab → **Create access key**
7. Select **"Application running outside AWS"** → **Create**
8. **Download/copy the Access Key ID and Secret Access Key** (you can only see the secret once!)

### Step 5.2 — Add AWS Credentials to Jenkins

1. Go to **Dashboard** → **Manage Jenkins** → **Credentials**
2. Click **(global)** → **Add Credentials**

| Field | Value |
|-------|-------|
| Kind | **AWS Credentials** |
| ID | `aws-credentials` |
| Description | `AWS credentials for S3 and EC2` |
| Access Key ID | Your `AKIA...` key |
| Secret Access Key | Your secret key |

3. Click **OK**

### Step 5.3 — Also add credentials as Secret Text (for shell scripts)

We need the credentials accessible in shell scripts too:

**Add Access Key ID:**
1. **Add Credentials** → Kind: **Secret text**
2. Secret: your Access Key ID
3. ID: `aws-access-key-id`
4. Description: `AWS Access Key ID`

**Add Secret Access Key:**
1. **Add Credentials** → Kind: **Secret text**
2. Secret: your Secret Access Key
3. ID: `aws-secret-access-key`
4. Description: `AWS Secret Access Key`

---

## Part 6: Set Up an EC2 as Jenkins Agent (Worker Node)

> This is the machine that will actually RUN the Black formatter job.

### Step 6.1 — Launch EC2 Instance for Agent

Go to **EC2 Dashboard** → **Launch Instance**:

| Setting | Value |
|---------|-------|
| **Name** | `jenkins-agent` |
| **AMI** | Ubuntu Server 22.04 LTS |
| **Instance Type** | `t2.micro` (1 vCPU, 1 GB — sufficient for running Black) |
| **Key Pair** | Use the same `jenkins-key` |
| **Security Group** | Allow SSH (port 22) from Jenkins Master's Security Group |
| **Storage** | 10 GB gp3 |

### Step 6.2 — SSH into the Agent and install dependencies

```bash
# SSH into the agent
ssh -i jenkins-key.pem ubuntu@<AGENT-PUBLIC-IP>
```

Run these commands on the **agent machine**:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Java (required for Jenkins agent)
sudo apt install -y fontconfig openjdk-17-jre

# Install Python 3, pip, and venv
sudo apt install -y python3 python3-pip python3-venv

# Install black globally
sudo pip3 install black

# Verify installations
java -version
python3 --version
black --version

# Install AWS CLI (for uploading logs to S3)
sudo apt install -y unzip curl
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version

# Install Git
sudo apt install -y git

# Create Jenkins agent working directory
sudo mkdir -p /home/jenkins/agent
sudo chown ubuntu:ubuntu /home/jenkins/agent
```

### Step 6.3 — Set up SSH key for Jenkins Master → Agent connection

**On your local machine (Jenkins Master):**

```bash
# Generate SSH key pair (press Enter for all prompts — no passphrase)
sudo -u jenkins ssh-keygen -t rsa -b 4096 -f /var/lib/jenkins/.ssh/id_rsa -N ""
```

```bash
# Display the public key (copy this!)
sudo cat /var/lib/jenkins/.ssh/id_rsa.pub
```

**On the Jenkins Agent EC2:**

```bash
# Paste the public key into authorized_keys
echo "<PASTE-PUBLIC-KEY-HERE>" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

**Back on your local machine — test the connection:**

```bash
sudo -u jenkins ssh -o StrictHostKeyChecking=no ubuntu@<AGENT-PRIVATE-IP>
# Should connect without password. Type 'exit' to return.
```

### Step 6.4 — Add SSH credentials to Jenkins

1. Go to **Dashboard** → **Manage Jenkins** → **Credentials** → **(global)** → **Add Credentials**

| Field | Value |
|-------|-------|
| Kind | **SSH Username with private key** |
| ID | `jenkins-agent-ssh` |
| Description | `SSH key for Jenkins agent` |
| Username | `ubuntu` |
| Private Key | **Enter directly** → paste content of `/var/lib/jenkins/.ssh/id_rsa` |

Get the private key:
```bash
sudo cat /var/lib/jenkins/.ssh/id_rsa
```

---

## Part 7: Connect the Agent Node in Jenkins

### Step 7.1 — Add the agent node

1. Go to **Dashboard** → **Manage Jenkins** → **Nodes** → **New Node**

| Field | Value |
|-------|-------|
| Node name | `python-agent` |
| Type | **Permanent Agent** |

2. Click **Create**

### Step 7.2 — Configure the agent

| Field | Value | Explanation |
|-------|-------|-------------|
| Description | `EC2 agent for running Python formatting` | Just a description |
| # of executors | `2` | Number of jobs this agent can run at once |
| Remote root directory | `/home/jenkins/agent` | Where Jenkins stores files on the agent |
| Labels | `python-agent` | We use this label in Jenkinsfile to target this agent |
| Usage | **Only build jobs with label expressions matching this node** | Jobs must explicitly request this agent |
| Launch method | **Launch agents via SSH** | How Jenkins connects to the agent |
| Host | `<AGENT-PRIVATE-IP>` | The private IP of your agent EC2 |
| Credentials | Select `jenkins-agent-ssh` | The SSH credential you added |
| Host Key Verification Strategy | **Non verifying** | Simplifies first connection |

3. Click **Save**
4. Go back to **Nodes** → Click `python-agent` → Click **"Launch agent"**
5. Check the log — it should say **"Agent successfully connected"**

---

## Part 8: Set Up the S3 Bucket for Log Storage

### Step 8.1 — Create the S3 bucket

1. Go to **AWS Console** → **S3** → **Create bucket**

| Setting | Value |
|---------|-------|
| Bucket name | `jenkins-black-logs-<your-account-id>` (must be globally unique) |
| AWS Region | Same region as your EC2 agent instance |
| Block all public access | **Keep checked** (logs should be private) |
| Versioning | Disabled |
| Encryption | SSE-S3 (default) |

2. Click **Create bucket**

### Step 8.2 — Configure AWS CLI on the Agent

SSH into the **agent EC2** and configure AWS CLI:

```bash
aws configure
```

Enter when prompted:
```
AWS Access Key ID: AKIA________________
AWS Secret Access Key: ________________________________________
Default region name: us-east-1           (your region)
Default output format: json
```

### Step 8.3 — Test S3 access from agent

```bash
# List buckets (should show your new bucket)
aws s3 ls

# Test upload
echo "test log" > /tmp/test.log
aws s3 cp /tmp/test.log s3://jenkins-black-logs-<your-account-id>/test/test.log
aws s3 ls s3://jenkins-black-logs-<your-account-id>/test/

# Clean up test
aws s3 rm s3://jenkins-black-logs-<your-account-id>/test/test.log
rm /tmp/test.log
```

---

## Part 9: Set Up GitHub Credentials

### Step 9.1 — Create a GitHub Personal Access Token (PAT)

1. Go to **GitHub** → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens**
2. Click **"Generate new token"**

| Setting | Value |
|---------|-------|
| Token name | `jenkins-pipeline` |
| Expiration | 90 days (or custom) |
| Repository access | **Only select repositories** → Select your repo |
| Permissions | |
| → Contents | Read-only |
| → Pull requests | Read and Write |
| → Webhooks | Read and Write |
| → Commit statuses | Read and Write |

3. Click **Generate token**
4. **Copy the token!** (starts with `github_pat_` or `ghp_`)

### Step 9.2 — Add GitHub credentials to Jenkins

1. Go to **Dashboard** → **Manage Jenkins** → **Credentials** → **(global)** → **Add Credentials**

| Field | Value |
|-------|-------|
| Kind | **Username with password** |
| Username | Your GitHub username |
| Password | Your GitHub Personal Access Token |
| ID | `github-credentials` |
| Description | `GitHub PAT for repo access` |

2. Click **OK**

---

## Part 10: Create the Git Repository

### Step 10.1 — Create the repo on GitHub

1. Go to **GitHub** → **New repository**
2. Name: `jenkins-black-formatter`
3. Visibility: **Public** or **Private**
4. **Do NOT** initialize with README (we'll push our local code)
5. Click **Create repository**

### Step 10.2 — Push the local project to GitHub

This project contains all the files you need. Run from the project root:

```bash
cd /path/to/jenkins-black-formatter

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Jenkins Black formatter pipeline"

# Add remote (replace with YOUR repo URL)
git remote add origin https://github.com/<YOUR-USERNAME>/jenkins-black-formatter.git

# Push to main
git branch -M main
git push -u origin main
```

---

## Part 11: Understand the Jenkinsfile

See the `Jenkinsfile` in this repo. Here's what each section does:

```
pipeline {
    agent { label 'python-agent' }    ← Run on our EC2 agent node
    
    triggers {
        cron('H/30 * * * *')          ← Also run every 30 minutes
    }
    
    stages {
        stage('Checkout') { ... }      ← Pull code from Git
        stage('Install') { ... }       ← Install Python dependencies (black)
        stage('Format Check') { ... }  ← Run black --check on all .py files
        stage('Upload Logs') { ... }   ← Upload results to S3
    }
    
    post {
        always { ... }                 ← Clean up after every run
    }
}
```

### Key Concepts:

| Concept | Explanation |
|---------|-------------|
| `agent { label 'python-agent' }` | Only run this job on the agent node with the label `python-agent` |
| `triggers { cron('H/30 * * * *') }` | Jenkins cron: run every 30 minutes. `H` means Jenkins picks a minute to spread load |
| `stage(...)` | A named step in the pipeline. Appears as a column in the Stage View |
| `steps { sh '...' }` | Runs a shell command on the agent |
| `post { always { ... } }` | Runs after the pipeline, no matter if it succeeded or failed |
| `environment { ... }` | Defines environment variables available in all stages |
| `credentials(...)` | Securely injects stored credentials as environment variables |

---

## Part 12: Create the Multibranch Pipeline in Jenkins

> A **Multibranch Pipeline** automatically discovers branches and PRs in your GitHub repo.

### Step 12.1 — Create the pipeline

1. Go to **Dashboard** → **New Item**
2. Enter name: `black-formatter`
3. Select **"Multibranch Pipeline"**
4. Click **OK**

### Step 12.2 — Configure Branch Sources

1. Under **Branch Sources**, click **"Add source"** → **GitHub**

| Field | Value |
|-------|-------|
| Credentials | Select `github-credentials` |
| Repository HTTPS URL | `https://github.com/<YOUR-USERNAME>/jenkins-black-formatter.git` |

2. Under **Behaviors**, make sure these are included:
   - **Discover branches** → Strategy: All branches
   - **Discover pull requests from origin** → Strategy: Merging the PR with the target branch

### Step 12.3 — Configure Build Configuration

| Field | Value |
|-------|-------|
| Mode | **by Jenkinsfile** |
| Script Path | `Jenkinsfile` |

### Step 12.4 — Configure Scan Triggers

Under **Scan Multibranch Pipeline Triggers**:
- Check **"Periodically if not otherwise run"**
- Interval: **1 minute** (for quick PR discovery)

### Step 12.5 — Save

Click **"Save"**. Jenkins will immediately scan your repo and find the `main` branch.

---

## Part 13: Configure GitHub Webhooks for PR Triggers

> Webhooks make GitHub notify Jenkins instantly when a PR is opened/updated.

### Step 13.1 — Configure Jenkins for webhooks

1. Go to **Dashboard** → **Manage Jenkins** → **System**
2. Scroll to **"GitHub"** section
3. Click **"Add GitHub Server"**

| Field | Value |
|-------|-------|
| Name | `github` |
| API URL | `https://api.github.com` |
| Credentials | Select your GitHub credentials |

4. Check **"Manage hooks"** 
5. Click **Save**

### Step 13.2 — Add webhook in GitHub (if automatic doesn't work)

1. Go to your GitHub repo → **Settings** → **Webhooks** → **Add webhook**

| Field | Value |
|-------|-------|
| Payload URL | `http://<YOUR-PUBLIC-IP>:8080/github-webhook/` |
| Content type | `application/json` |
| Which events? | Select **"Let me select individual events"** → check **Pull requests** and **Pushes** |
| Active | Checked |

2. Click **"Add webhook"**

---

## Part 14: Test the Pipeline

### Step 14.1 — Create a test branch and PR

```bash
# Create new branch
git checkout -b feature/test-formatting

# Make a change to a Python file (intentionally bad formatting)
echo "x=1;y=2;z=x+y" >> src/app.py

# Commit and push
git add .
git commit -m "Test: bad formatting"
git push origin feature/test-formatting
```

### Step 14.2 — Create PR on GitHub

1. Go to your repo on GitHub
2. Click **"Compare & pull request"**
3. Create the PR

### Step 14.3 — Watch Jenkins

1. Go to Jenkins → `black-formatter` pipeline
2. You should see a new branch/PR being built
3. Click on it to see the stages
4. The "Format Check" stage should **FAIL** because `x=1;y=2;z=x+y` is not black-formatted

### Step 14.4 — Check S3 logs

```bash
# On the agent or any machine with AWS CLI
aws s3 ls s3://jenkins-black-logs-<your-account-id>/logs/ --recursive
```

---

## Part 15: Common Commands Reference

### Jenkins Service Commands

```bash
# Start Jenkins
sudo systemctl start jenkins

# Stop Jenkins
sudo systemctl stop jenkins

# Restart Jenkins
sudo systemctl restart jenkins

# Check status
sudo systemctl status jenkins

# View Jenkins logs
sudo journalctl -u jenkins -f

# View Jenkins log file
sudo tail -f /var/log/jenkins/jenkins.log
```

### Jenkins File Locations

```bash
/var/lib/jenkins/                  # Jenkins home directory
/var/lib/jenkins/workspace/        # Where jobs run
/var/lib/jenkins/jobs/             # Job configurations
/var/lib/jenkins/plugins/          # Installed plugins
/var/lib/jenkins/secrets/          # Secrets and keys
/var/lib/jenkins/config.xml        # Main config file
/var/log/jenkins/jenkins.log       # Log file
/etc/default/jenkins               # Jenkins defaults (port, args)
```

### Python & Black Commands

```bash
# Install black
pip3 install black

# Check formatting (doesn't modify files)
black --check .

# Check with diff (shows what would change)
black --check --diff .

# Actually format files (modifies them)
black .

# Check specific directory
black --check src/ tests/

# Check with specific line length
black --check --line-length 88 .

# Show version
black --version
```

### AWS CLI Commands

```bash
# Configure AWS CLI
aws configure

# List S3 buckets
aws s3 ls

# Upload file to S3
aws s3 cp local-file.log s3://bucket-name/path/file.log

# List S3 bucket contents
aws s3 ls s3://bucket-name/ --recursive

# Download from S3
aws s3 cp s3://bucket-name/path/file.log ./local-file.log

# Sync directory to S3
aws s3 sync ./logs/ s3://bucket-name/logs/
```

### Git Commands

```bash
# Clone repository
git clone https://github.com/<user>/<repo>.git

# Create branch
git checkout -b feature/my-feature

# Stage changes
git add .

# Commit
git commit -m "message"

# Push
git push origin feature/my-feature

# Pull latest
git pull origin main

# Check status
git status

# View log
git log --oneline -10
```

### EC2 Agent / SSH Commands

```bash
# SSH into agent instance
ssh -i key.pem ubuntu@<IP>

# Copy file to EC2 agent
scp -i key.pem local-file ubuntu@<IP>:/remote/path/

# Check disk space
df -h

# Check memory
free -h

# Check running processes
htop  # or: ps aux

# Check ports
sudo netstat -tlnp
```

---

## Part 16: Troubleshooting

### Jenkins won't start

```bash
# Check if port 8080 is in use
sudo lsof -i :8080

# Check Jenkins logs for errors
sudo journalctl -u jenkins --no-pager | tail -50

# Check Java version
java -version

# Make sure Jenkins user has permissions
sudo chown -R jenkins:jenkins /var/lib/jenkins
```

### Agent won't connect

```bash
# Test SSH from local machine to agent
sudo -u jenkins ssh ubuntu@<AGENT-IP>

# Check if Java is installed on agent
ssh -i jenkins-key.pem ubuntu@<AGENT-IP> "java -version"

# Check agent logs in Jenkins UI
# Dashboard → Nodes → python-agent → Log
```

### Pipeline fails at "Install Dependencies"

```bash
# SSH to agent and verify pip works
python3 -m pip --version

# Try installing black manually
pip3 install black

# Check Python version
python3 --version
```

### S3 upload fails

```bash
# Check AWS CLI configuration
aws configure list

# Test S3 access
aws s3 ls

# Check IAM permissions
aws sts get-caller-identity
```

### Webhook not triggering

1. Check GitHub webhook deliveries:
   - Repo → Settings → Webhooks → Click webhook → Recent Deliveries
2. Check Jenkins is accessible from internet (you may need to use a tunneling service like ngrok):
   ```bash
   curl http://<YOUR-PUBLIC-IP>:8080/github-webhook/
   ```
3. If running on a local machine, ensure port 8080 is forwarded or use a tunneling service

### Common errors and fixes

| Error | Fix |
|-------|-----|
| `java.lang.OutOfMemoryError` | Increase system memory or allocate more to Jenkins |
| `Permission denied (publickey)` | Check SSH key is correct and `authorized_keys` permissions are 600 |
| `black: command not found` | Install black: `pip3 install black` or use full path `/usr/local/bin/black` |
| `No such bucket` | Check bucket name spelling and region |
| `Access Denied` to S3 | Check IAM policy has `s3:PutObject` permission |
| `JNLP agent not connected` | Use SSH launch method instead of JNLP |

---

## Summary of All Credentials Needed

| Credential | Where It's Used | How to Get It |
|------------|-----------------|---------------|
| Jenkins Admin Password | Initial Jenkins setup | `sudo cat /var/lib/jenkins/secrets/initialAdminPassword` |
| AWS Access Key ID | S3 log upload, EC2 agents | AWS IAM → Create Access Key |
| AWS Secret Access Key | S3 log upload, EC2 agents | AWS IAM → Create Access Key (shown once!) |
| GitHub PAT | Jenkins → GitHub repo access | GitHub → Settings → Developer Settings → PATs |
| SSH Private Key | Jenkins Master → Agent connection | `ssh-keygen` on your local machine |
| EC2 Key Pair (.pem) | SSH into agent EC2 instance | Created when launching EC2 |

---

**Congratulations!** You now have a complete Jenkins setup that:
- ✅ Runs Jenkins Master on your local machine (laptop)
- ✅ Uses a dedicated EC2 agent node for running jobs
- ✅ Checks Python formatting with Black on every PR
- ✅ Runs every 30 minutes
- ✅ Stores logs in S3

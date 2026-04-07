// This Jenkinsfile defines a pipeline that:
// 1. Runs on the 'python-agent' EC2 node
// 2. Checks Python formatting with 'black' on all .py files
// 3. Triggers on PRs and every 30 minutes
// 4. Uploads logs to S3

pipeline {
    // Run ONLY on the EC2 agent node labeled 'python-agent'
    agent {
        label 'python-agent'
    }

    // Environment variables available in all stages
    environment {
        // Name of your S3 bucket (CHANGE THIS to your actual bucket name)
        S3_BUCKET = 'jenkins-black-logs-423623858641'
        // AWS region
        AWS_DEFAULT_REGION = 'us-east-1'
        // Inject AWS credentials from Jenkins credential store
        AWS_ACCESS_KEY_ID = credentials('aws-access-key-id')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-access-key')
    }

    // Triggers: run every 30 minutes AND on PR events (via webhook)
    triggers {
        // H/30 = every 30 minutes. 'H' lets Jenkins pick which minute
        // to spread the load across multiple jobs
        // Minute Hour DayOfMonth Month DayOfWeek
        cron('H/30 * * * *')
    }

    options {
        // Keep only the last 10 builds to save disk space
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // Add timestamps to console output
        timestamps()
        // Abort the build if it takes longer than 15 minutes
        timeout(time: 15, unit: 'MINUTES')
    }

    stages {
        // ── Stage 1: Checkout the source code ──
        stage('Checkout') {
            steps {
                // Pull the code from the Git repository
                // For multibranch pipelines, this checks out the PR branch
                checkout scm
                sh 'echo "Checked out branch: ${GIT_BRANCH}"'
                sh 'echo "Commit: $(git rev-parse HEAD)"'
            }
        }

        // ── Stage 2: Install Python dependencies ──
        stage('Install Dependencies') {
            steps {
                sh '''
                    echo "=== Installing Python dependencies ==="
                    # Install black globally from requirements.txt
                    sudo pip3 install -r requirements.txt --break-system-packages
                    # Verify black is installed and accessible
                    black --version
                    echo "=== Dependencies installed successfully ==="
                '''
            }
        }

        // ── Stage 3: Run Black formatter check ──
        stage('Format Check') {
            steps {
                sh '''
                    echo "=== Running Black format check on all Python files ==="

                    # Find all Python files and display them
                    echo "Python files found:"
                    find . -name "*.py" | sort
                    echo ""

                    # Run black in check mode (does NOT modify files)
                    # --check: exits with error code 1 if files need formatting
                    # --diff:  shows what changes would be made
                    # --color: colored output for readability
                    # Tee output to a log file for S3 upload
                    black --check --diff --color . \
                        2>&1 | tee black-report.log

                    echo ""
                    echo "=== Black format check completed ==="
                '''
            }
        }

        // ── Stage 4: Upload logs to S3 ──
        stage('Upload Logs to S3') {
            // Run this stage even if the previous stage failed
            // (we want logs uploaded regardless)
            when {
                expression { return true }
            }
            steps {
                sh '''
                    echo "=== Uploading logs to S3 ==="

                    # Create metadata file with build info
                    cat > build-info.json << EOF
{
    "job_name": "${JOB_NAME}",
    "build_number": "${BUILD_NUMBER}",
    "build_url": "${BUILD_URL}",
    "git_branch": "${GIT_BRANCH}",
    "git_commit": "$(git rev-parse HEAD)",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "node_name": "${NODE_NAME}"
}
EOF

                    # Upload black report to S3
                    aws s3 cp black-report.log \
                        "s3://${S3_BUCKET}/logs/${JOB_NAME}/${BUILD_NUMBER}/black-report.log" \
                        --content-type "text/plain"

                    # Upload build info to S3
                    aws s3 cp build-info.json \
                        "s3://${S3_BUCKET}/logs/${JOB_NAME}/${BUILD_NUMBER}/build-info.json" \
                        --content-type "application/json"

                    echo "Logs uploaded to: s3://${S3_BUCKET}/logs/${JOB_NAME}/${BUILD_NUMBER}/"
                    echo "=== Upload complete ==="
                '''
            }
        }
    }

    // ── Post actions: run after all stages ──
    post {
        // Always run these steps (success or failure)
        always {
            // Upload the full console log to S3
            sh '''
                # Save console log URL for reference
                echo "Full console log: ${BUILD_URL}console" > console-url.txt
                aws s3 cp console-url.txt \
                    "s3://${S3_BUCKET}/logs/${JOB_NAME}/${BUILD_NUMBER}/console-url.txt" \
                    --content-type "text/plain" || true
            '''
            // Clean up workspace
            cleanWs()
        }

        // On success
        success {
            echo 'Black formatting check PASSED! All Python files are properly formatted.'
        }

        // On failure
        failure {
            echo 'Black formatting check FAILED! Some Python files need formatting.'
            echo 'Run "black ." locally to fix formatting issues.'
        }
    }
}

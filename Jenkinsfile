pipeline {
agent any


triggers {
    cron('0 17 * * 6')
}

environment {
    PYTHONUNBUFFERED = '1'
}

stages {

    stage('Check Alternate Week') {
        steps {
            script {
                def day = sh(
                    script: "date +%d",
                    returnStdout: true
                ).trim().toInteger()

                if (!((day >= 8 && day <= 14) || (day >= 22 && day <= 28))) {
                    currentBuild.result = 'NOT_BUILT'
                    error("Not 2nd or 4th Saturday — skipping run")
                }

                echo "Valid 2nd/4th Saturday"
            }
        }
    }

    stage('Checkout') {
        steps {
            git branch: 'main',
                url: 'https://github.com/adityaBhatt02/aws-account-automation-playwright'
        }
    }

    stage('Setup') {
        steps {

            withCredentials([
                file(credentialsId: 'aws-env-file',
                variable: 'ENV_FILE')
            ]) {
                sh 'cp $ENV_FILE .env'
            }

            sh '''
                python3 -m venv venv
                . venv/bin/activate

                pip install -r requirements.txt
                playwright install chromium
            '''
        }
    }

    stage('Run Account Creator') {
        steps {
            sh '''
                . venv/bin/activate

                export DISPLAY=:99
                Xvfb :99 -screen 0 1920x1080x24 &
                sleep 2

                export AWS_ACCOUNT_COUNT=$(grep AWS_ACCOUNT_COUNT .env | cut -d '=' -f2 | tr -d '"')
                export AWS_ACCOUNT_TYPE_KEY=$(grep AWS_ACCOUNT_TYPE_KEY .env | cut -d '=' -f2 | tr -d '"')

                echo "[Jenkins] Account Count: $AWS_ACCOUNT_COUNT"
                echo "[Jenkins] Account Type Key: $AWS_ACCOUNT_TYPE_KEY"

                set -o pipefail

                python3 main.py 2>&1 | tee run_output.txt
            '''
        }
    }
}

post {

    always {

        archiveArtifacts(
            artifacts: '''
                generated_accounts.csv,
                run_output.txt,
                screenshots/**/*.png,
                playwright-report/**,
                test-results/**
            ''',
            allowEmptyArchive: true
        )

        sh 'rm -f .env || true'
    }

    success {

        mail(
            to: 'itsadityayayaya@gmail.com',
            subject: "AWS Account Creator SUCCESS #${BUILD_NUMBER}",
            body: """


AWS Account Creator completed successfully.

Job: ${JOB_NAME}
Build: #${BUILD_NUMBER}

Console:
${BUILD_URL}console

Artifacts:
${BUILD_URL}artifact/

CSV:
${BUILD_URL}artifact/generated_accounts.csv
"""
)
}


    failure {

        mail(
            to: 'itsadityayayaya@gmail.com',
            subject: "AWS Account Creator FAILED #${BUILD_NUMBER}",
            body: """


AWS Account Creator failed.

Job: ${JOB_NAME}
Build: #${BUILD_NUMBER}

Console:
${BUILD_URL}console

Artifacts:
${BUILD_URL}artifact/

Screenshots:
${BUILD_URL}artifact/screenshots/

Playwright Report:
${BUILD_URL}artifact/playwright-report/

Logs:
${BUILD_URL}artifact/run_output.txt
"""
)
}
}
}

pipeline {
    agent any

    triggers {
        cron('0 9 * * 6')
    }

    environment {
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Check Alternate Week') {
            steps {
                script {
                    def weekNum = sh(script: "date +%V", returnStdout: true).trim().toInteger()
                    if (weekNum % 2 != 0) {
                        currentBuild.result = 'NOT_BUILT'
                        error("Odd week ${weekNum} — skipping this run")
                    }
                    echo "Week ${weekNum} — proceeding"
                }
            }
        }

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/adityaBhatt02/aws-account-automation-playwright'
            }
        }

        stage('Setup') {
            steps {
                withCredentials([file(credentialsId: 'aws-env-file', variable: 'ENV_FILE')]) {
                    sh 'cp $ENV_FILE .env'
                }
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt --quiet
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

                    python3 main.py 2>&1 | tee run_output.txt
                '''
            }
        }
    }

    post {
        success {
            script {
                def output = readFile('run_output.txt')
                def csvContent = fileExists('generated_accounts.csv') ? readFile('generated_accounts.csv') : 'No CSV generated'

                emailext(
                    to: 'itsadityayayaya@gmail.com , diya.khandelwal@cloudkeeper.com',
                    subject: "AWS Account Creator — SUCCESS [Build #${BUILD_NUMBER}]",
                    body: """
AWS Account Auto-Creator completed successfully.

Build: #${BUILD_NUMBER}
Date: ${new Date()}

--- Script Output ---
${output.take(3000)}

--- Accounts Created (CSV) ---
${csvContent}

Full logs: ${BUILD_URL}console
                    """,
                    attachmentsPattern: 'generated_accounts.csv'
                )
            }
        }

        failure {
            script {
                def output = fileExists('run_output.txt') ? readFile('run_output.txt') : 'No output captured'

                def stepPatterns = [
                    'STEP 1: SIGNUP',
                    'STEP 2: PLAN SELECTION',
                    'STEP 3: CONTACT INFO',
                    'STEP 4: BILLING',
                    'STEP 5: IDENTITY VERIFICATION',
                    'STEP 6: 3DS CARD VERIFICATION',
                    'STEP 7: SUPPORT PLAN',
                    'STEP 8: WAITING FOR ACCOUNT CREATION'
                ]

                def lastStep = 'Unknown'
                stepPatterns.each { step ->
                    if (output.contains(step)) lastStep = step
                }

                def errorLine = output.split('\n')
                    .findAll { it.contains('❌') || it.contains('FAILED') || it.contains('Exception') }
                    .join('\n')
                    .take(500)

                // FIX: replaced .takeRight() with plain split + size math (sandbox safe)
                def lines = output.split('\n')
                def startIdx = lines.size() > 100 ? lines.size() - 100 : 0
                def lastLines = lines[startIdx..<lines.size()].join('\n')

                emailext(
                    to: 'itsadityayayaya@gmail.com',
                    subject: "❌ AWS Account Creator — FAILED [Build #${BUILD_NUMBER}]",
                    body: """
AWS Account Auto-Creator FAILED.

Build: #${BUILD_NUMBER}
Date: ${new Date()}

--- Last Step Reached ---
${lastStep}

--- Error Details ---
${errorLine ?: 'See full logs below'}

--- Last 100 Lines of Output ---
${lastLines}

Full logs: ${BUILD_URL}console
                    """
                )
            }
        }

        always {
            archiveArtifacts artifacts: 'generated_accounts.csv,debug_*.png', allowEmptyArchive: true
            sh 'rm -f .env'
        }
    }
}

pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh 'exit 1'
            }
        }
    }

    post {
        failure {
            mail(
                to: 'itsadityayayaya@gmail.com',
                subject: 'MAIL STEP TEST',
                body: 'Hello'
            )
        }
    }
}

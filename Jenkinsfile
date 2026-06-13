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
            emailext(
                to: 'itsadityayayaya@gmail.com',
                subject: "FAILURE TEST ${BUILD_NUMBER}",
                body: "Hello from Jenkins"
            )
        }
    }
}


pipeline {
    agent any

    stages {
        stage('Setup Python') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Run Automated Tests') {
            steps {
                sh '''
                    bash run_tests.sh
                '''
            }
        }
    }

   
post {
    always {
        junit allowEmptyResults: false,
              testResults: 'test-results.xml'
    }

    success {
        echo 'SUCCESS: All tests passed!'
    }

    failure {
        echo 'FAILED: Check the test results.'
    }
}

}

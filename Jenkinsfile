#!/usr/bin/groovy

boolean continuePipeline = false
def nodeLabel = 'ci-python-36'

jenkinsTemplate(nodeLabel, ['docker', 'python36']) {
    node(nodeLabel) {
        checkout scm

        stage ('Building package') {
            container('python36') {
                sh 'python setup.py sdist'
            }
        }

        stage ('Publish on PyPi') {
            withCredentials([file(credentialsId: 'pypirc', variable: 'pypirc')]) {
                container('python36') {
                    sh 'pip install twine'
                    sh "twine upload --config-file $pypirc --repository internal dist/*"
                }
            }
        }
    }
}
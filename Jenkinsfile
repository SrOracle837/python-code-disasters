pipeline {
    agent any
    
    environment {
        SONAR_PROJECT_KEY = 'python-code-disasters'
        DATAPROC_NAME = 'ayush-mani-dataproc'
        DATAPROC_BUCKET = 'ayush-mani-bucket'
        PROJECT_ID = 'turnkey-guild-472303-i3'
        REGION = 'us-central1'
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    def causes = currentBuild.getBuildCauses()
                    echo "Stage triggered by: ${causes}"                
                    def isWebhook = causes.toString().contains('GitHubPushCause')
                    def isPolling = causes.toString().contains('SCMTrigger')
                }                
                checkout scm
            }
        }
        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('SonarQube') {
                        sh """
                            ${scannerHome}/bin/sonar-scanner \
                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                            -Dsonar.sources=. \
                            -Dsonar.python.version=3 \
                            -Dsonar.exclusions=**/*.md,**/*.txt,**/*.xml,**/*.json,**/tests/**
                        """
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            env.RUN_HADOOP = 'false'
                        } else {
                            env.RUN_HADOOP = 'true'
                        }
                    }
                }
            }
        }
        

        stage('Trigger Hadoop Job') {
            when { expression { env.RUN_HADOOP == 'true' } }
            steps {
                script {
                    sh """
                    gcloud config set project ${PROJECT_ID}
                    gcloud storage rm -r gs://${DATAPROC_BUCKET}/input || true
                    gcloud storage cp '**/*.py' gs://${DATAPROC_BUCKET}/input/ --recursive
                    gcloud dataproc jobs submit hadoop \
                        --project=${PROJECT_ID} \
                        --region=${REGION} \
                        --cluster=${DATAPROC_NAME} \
                        --class=org.apache.hadoop.streaming.HadoopStreaming \
                        -- \
                        -files gs://${DATAPROC_BUCKET}/scripts/mapper.py,gs://${DATAPROC_BUCKET}/scripts/reducer.py \
                        -mapper "python3 mapper.py" \
                        -reducer "python3 reducer.py" \
                        -input gs://${DATAPROC_BUCKET}/input \
                        -output gs://${DATAPROC_BUCKET}/output-$BUILD_NUMBER
                    gcloud storage cat gs://${DATAPROC_BUCKET}/output-$BUILD_NUMBER/part-*
                    """
                }
            }
        }
    }
    
    post {
        always {
            echo "Build run status: ${currentBuild.result}"
            echo "Hadoop run status: ${env.RUN_HADOOP ?: 'NO (as SonarQube analysis flagged it)'}"
        }
    }
}

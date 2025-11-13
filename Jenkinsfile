pipeline {
    agent any
    environment {
        SONAR_PROJECT_KEY = 'python-code-disasters'
        DATAPROC_NAME = 'ayush-mani-dataproc'
        DATAPROC_BUCKET = 'ayush-mani-bucket'
        PROJECT_ID = 'turnkey-guild-472303-i3'
        REGION = 'us-central1'
        ZONE = 'us-central1-f'
    } 
    stages {
        stage('GH Checkout') {
            steps {
                script {
                    def causes = currentBuild.getBuildCauses()
                    echo "Stage started by: ${causes}"                
                    def isWebhook = causes.toString().contains('GitHubPushCause')
                    def isPolling = causes.toString().contains('SCMTrigger')
                }                
                checkout scm
            }
        }
        stage('SonarQube') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('SonarQube') {
                        sh """
                            ${scannerHome}/bin/sonar-scanner -Dsonar.projectKey=${SONAR_PROJECT_KEY} -Dsonar.sources=.                         
                            """
                    }
                }
            }
        }
        stage('SonarQube Results') {
            steps {
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
        stage('Hadoop Job') {
            when { expression { env.RUN_HADOOP == 'true' } }
            steps {
                script {
                    sh """
                    gcloud config set project ${PROJECT_ID}
                    gcloud storage rm -r gs://${DATAPROC_BUCKET}/output-${BUILD_NUMBER} || true
                    mkdir -p inputs
                    find . -name "*.py" -exec cp {} inputs/ \\;
                    gcloud compute ssh ${DATAPROC_NAME}-m --zone=${ZONE} --command="rm -rf ~/inputs && mkdir -p ~/inputs"
                    gcloud compute scp inputs/* ${DATAPROC_NAME}-m:~/inputs/ --zone=${ZONE}
                    gcloud compute ssh "${DATAPROC_NAME}-m" --zone="${ZONE}" --command="hadoop fs -rm -r /input || true && hadoop fs -mkdir -p /input && hadoop fs -put ~/inputs/* /input/"
                    rm -rf inputs
                    gcloud dataproc jobs submit hadoop \
                        --project=${PROJECT_ID} \
                        --region=${REGION} \
                        --cluster=${DATAPROC_NAME} \
                        --jar=file:///usr/lib/hadoop/hadoop-streaming.jar \
                        -- \
                        -files hdfs:///scripts/mapper.py,hdfs:///scripts/reducer.py \
                        -mapper "python3 mapper.py" \
                        -reducer "python3 reducer.py" \
                        -input hdfs:///input \
                        -output gs://${DATAPROC_BUCKET}/output-${BUILD_NUMBER}
                    gcloud storage cat gs://${DATAPROC_BUCKET}/output-${BUILD_NUMBER}/part-*
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
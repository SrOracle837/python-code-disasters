pipeline {
    agent any
    environment {
        SONAR_PROJECT_KEY = 'python-code-disasters'
        DATAPROC_NAME = 'ayush-mani-dataproc'
        DATAPROC_BUCKET = 'ayush-mani-bucket'
        PROJECT_ID = 'projnewcloud'
        REGION = 'us-central1'
        ZONE = 'us-central1-f'
    }
    stages {
        stage('GH Checkout') {
            steps {
                script {
                    echo "Stage triggered by: ${currentBuild.getBuildCauses()}"                
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
        stage('SonarQube Result') {
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
        stage('Hadoop') {
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
                        -files gs://${DATAPROC_BUCKET}/scripts/mapper.py,gs://${DATAPROC_BUCKET}/scripts/reducer.py \
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

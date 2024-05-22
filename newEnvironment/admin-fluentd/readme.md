# Dockerfile
This image is based on the fluentd official image baded on debian, avoiding us to waste time compiling the image. It's completed adding the necessary packages for the analysis of the dos.log entries (tensorflow, scikit-learn, numpy and joblib).
# Entrypoint for fluentd
The entrypoint script is copied which means it is integrated in the fluentd image. To change it, the image needs to be built again as well. 
Finally it's made executable thanks to chmod.

### Entrypoint script
* Fluentd is start by using the configuration file present in the shared volume (refere to docker-compose.yml file or readme) and executed in background.
* Finally the sleep command is called.


# Conf
In the conf directory is present the fluent.conf file, which is used to start fluentd and specify the source of the logs and how to use them

# Output
Is the directory of the logs collecte by fluentd. Inside of it there are the generic logs of the entire network and the logs of the server related to the dos attacks (folder DoS).

# Shared-volume
Is a generic volume shared with the host. Inside of it is present a folder (prediction) containing all the scripts related to the classification of the dos.log entry in attack or non malicious.
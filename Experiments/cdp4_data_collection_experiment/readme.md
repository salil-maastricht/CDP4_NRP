

Follow those steps in order to get the CDP4 Loop Experiment running:

1. You will need to install the NRP 3.2 docker image. To do that, download the nrp_installer.sh script from (https://neurorobotics.net/downloads/nrp_installer.sh) and then execute it with the following commands:

	$ ./nrp_installer.sh update
	$ ./nrp_installer.sh install latest

2. Start your NRP Docker containers and access the NRP Frontend through https://localhost:9000/#/esv-web. If it's your first time to access the NRP Frontend, you'll have to provide the following login credentials
        username: nrpuser
        password: password

3. After accessing the NRP Frontend, navigate to the 'My experiments' tab and click on the 'Import folder' button. From there upload the entire cdp4_data_collection_experiment/ folder. Once the upload finishes, you should see the `CDP4 Data Collection Experiment` listed under the 'My Experiments' tab. Note that the upload can take a few seconds.

4. Exit the docker container and copy the saliency model from the root of the repository files.
	a. Exit the docker container
		`$ CTRL + D`

	b. Navigate to the root of the repository files and copy the "salmodel" directory to the experiment files inside the docker container
		`$ docker cp salmodel/ nrp:/home/bbpnrsoa/.opt/nrpStorage/cdp4_data_collection_experiment_0/resources/` 

5. Before starting the experiment, some additional models and packages need to be installed. For that you'd have to execute a script inside the NRP Backend Docker container. To do so, please execute the following commands inside a Terminal:

	a. The first step is to access the NRP Backend container
		`$ docker exec -it nrp bash`

	b. Navigate to the directory where the experiment files are located
		`$ cd /home/bbpnrsoa/.opt/nrpStorage/cdp4_data_collection_experiment_0`

	c. Make the install.sh script executable
		`$ chmod +x install.sh`

	d. Run the install.sh script. This will update apt packages, create a new virtualenv and install some pip packages
		`$ ./install.sh`

6. To run the experiment (spawning room layouts, moving the eyes, and saving data to disk), follow the following steps:

	a. Navigate to the experiment directory inside the docker container

   ```bash
            `$ cd /home/bbpnrsoa/.opt/nrpStorage/cdp4_data_collection_experiment_0/resources/
   ```
   
   b. (Optional) If you want to record a new dataset, make sure the dataset directory is deleted


```bash
			 `$ rm -rf /home/bbpnrsoa/cdp4_dataset`
```

​             If this directory exists and contains some data, running the experiment will amend the newly generated data to the existing dataset.

​       c. Run the run_experiment_script


```bash
			  `$ python run_experiment.py`
```

​            This script will launch the experiment, and inside a loop will select a random room/layout pair and spawn the corresponding objects. It will then           add the transfer function to the running simulation, and sleep for a certain amount of time. During this sleep period, the experiment will be running with the transfer function and data will be recorded to disk. You can modify this sleep time to increase or decrease the amount of data you want to record from one layout.
​            After waking up from the sleep period, the transfer function will be deleted, and the 3d objects will be deleted. Then, a new loop iteration will be started, where another room/layout pair will be selected, and so on.
​            The deletion of the transfer function during the spawning and deletion of 3d objects ensures, that data will only be recorded when rooms are fully spawned with objects      

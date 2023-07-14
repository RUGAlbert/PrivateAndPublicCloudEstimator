# PrivateAndPublicCloudEstimator


## Introduction
A lot of current software services use technologies facilitated by cloud computing. Cloud computing produces an increasing amount of emissions. Estimating the carbon footprint of cloud computing can be done by various models. However, it remains unclear which stakeholders bear responsibility for which part of the emissions, leaving the question of accountability unanswered.

In cooperation with BT Global Services, this project continued the development of a model to estimate the carbon emissions of cloud-based software services, and distribute them fairly among stakeholders. The estimate is made by splitting energy consumption into static energy usage, which cloud resources consume while idling, and dynamic energy usage, which is based on the actual usage pattern. Based on this, a lower and upper bound, together with a set of policies for deciding these bounds is defined with respect to which part of the energy consumption the stakeholder is responsible for. This provides the involved stakeholders with more insight on their footprint. On top of this, a new metric which clarifies how energy efficient a tenant uses a service in relation to other tenants is proposed. The use of this metric was evaluated by different stakeholders with respect to its efficacy.


## Usage

Before using the software first you will have to create a virtual environment and install all the packages in requirements.txt.

In order to use it you have to facilitate different files in one folder.
An example can be seen in testdata.
Then you have to run the following command:
```
python TCFPModel.py path/to/data
```

### CI
This is the carbon intenstiy file for the UK.
Currently only the Londen collumn is used

### Conccurent users
The maximum concurrent users on an half hour basis

### LondenUsage
The server watt usage on a hourly basis
If this is however on a minutely basis the 'useMinuteDataForPower' in config has to be set to true.

### Networkusage
The network usage in bytes per second

### Serverinfo

The metadata for the service
It always follows the same structure.

Below is an example

```
"servers": [
        {
            "name": "London",
            "DCEmissions": {
                "scope1": 0,
                "scope2":2857142856,
                "scope3": 846492
            },
            "PUE": 1.2,
            "energyServerStatic":238.4,
            "amountNetworkIsSharedBy":1,
            "backupNetworkEquipmentPowerUsage":85,
            "powerServerFile": "LondenUsage.csv",
            "networkUsageFile": "networkusage_LON.csv",
            "carbonIntensityFile": "CI.csv"
        }
    ],
    "concurrentUsersFile":"concurrentUser2.csv",
    "userTZ":1
}
```

* name: The name is the way you want to label it
* DCEmissions: The datacenter emissions split into the different scopes
* PUE: PUE of the datacenter
* energyServerStatic: The part of the energy which is static
* amountNetworkIsSharedBy: The amount of servers the network equipment is shared with
* backupNetworkEquipment: The watt usage of the backup network equipment not actively used
* powerServerFile: The file for the watt server usage
* networkUsageFile: the network usage for one location
* carbonIntensityFile: the file for the carbon intesntiy
* concurrentUsersFile: the concurrent users during that time
* userTZ: the timezone the data is in


### output
The output is a csv file for each server and one total.
Each of them has the following collumns:

*time: The timestamp of that moment
*scope2E: The total scope 2 energy consumption
*eServerStatic: the static part of the server energy consumption
*eServerDynamic: the dynamic part of the server energy consumption
*eNetworkStatic: the static part of the network energy consumption
*eNetworkDynamic: the dynamic part of the network energy consumption
*eCoolingStatic: the static part of the cooling energy consumption
*eCoolingDynamic: the dynamic part of the cooling energy consumption
*scope1: the Scope 1 emissions
*scope2Lower: the lower bound of Scope 2 emissions based on the policy
*scope2Upper: the upper bound of Scope 2 emissions based on the policy
*scope3: the Scope 3 emissions.
*TCFPLower: the lower bound of the total carbon footprint
*TCFPUpper: the upper bound of the total carbon footprint
*ci: the carbon intensity during that hour
*maxUsers: the amount of max users
*TCFPLowerPerUser: the lower bound of the total carbon footprint per user
*TCFPUpperPerUser: the upper bound of the total carbon footprint per user
*scope2EPerUser: the scope 2 energy consumption per user

As well that a prompt will be given with the different UPES scores like the following:
```
mSQR of  0.9988614954920007 for a n-value of  1.05
Area score 27.625588432482054
95 percent is less than 78.89913665383224
50 percent is less than 30.09910669661668
5 percent is less than 12.402728049359856
percentages of different components: Server: 0.58 Network: 0.27 Cooling: 0.16
percentages of static/dynamic 0.85 0.15
```
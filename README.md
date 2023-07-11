# PrivateAndPublicCloudEstimator


## Introduction
A lot of current software services use technologies facilitated by cloud computing. Cloud computing produces an increasing amount of emissions. Estimating the carbon footprint of cloud computing can be done by various models. However, it remains unclear which stakeholders bear responsibility for which part of the emissions, leaving the question of accountability unanswered.

In cooperation with BT Global Services, this project continued the development of a model to estimate the carbon emissions of cloud-based software services, and distribute them fairly among stakeholders. The estimate is made by splitting energy consumption into static energy usage, which cloud resources consume while idling, and dynamic energy usage, which is based on the actual usage pattern. Based on this, a lower and upper bound, together with a set of policies for deciding these bounds is defined with respect to which part of the energy consumption the stakeholder is responsible for. This provides the involved stakeholders with more insight on their footprint. On top of this, a new metric which clarifies how energy efficient a tenant uses a service in relation to other tenants is proposed. The use of this metric was evaluated by different stakeholders with respect to its efficacy.


## Usage

In order to use it you have to facilitate different files.
An example can be seen in testdata.

### CI
This is the carbon intenstiy file for the UK.
Currently only the Londen collumn is used

### Conccurent users
The maximum concurrent users on an half hour basis

### LondenUsage
The server watt usage on a hourly basis

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
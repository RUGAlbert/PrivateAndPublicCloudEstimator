# PrivateAndPublicCloudEstimator


## Questions
1-. Deos not use the VMeter model, despite claiming it does
2-. Everything is in energy except for the EMisc which already uses the carbon intensity
3. Net emissions are partly data centre based, and partly tentant based
4-. Multitenancy is circular
5. In the net energy it is just weird
6-. is idle time correct
7-. how is the model fitted?

Currently the total power usage is estimated using data from this report:
file:///C:/Users/alber/Downloads/kjna28874enn.pdf


## ServerInfo file explained

It is a list with all the servers with the following format:
"name": Name of the server,
"DCEmissions": {
"scope1": Scope 1 emissions of the entire data center per month
"scope3": Scope 2 emissions of the entire data center per month
},
"DCTotalEnergyUsage": Energy usage per month for the entire data center
"PUE": PUE of the data center
"powerServerFile": the file with the power usage data for the server,
"networkUsageFile": the file with the network usage data for the server

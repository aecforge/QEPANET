The focus of QEPANET is on allowing the user to easily create and manage EPANET projects inside QGIS. For this purpose, the development has been led by two principles:
1) using the standard EPANET inp file as a mean to save all the project data (therefore making it possible to open and edit existing inp files) and
2) creating an easy to use set of tools to guide the creation of the network, to ensure the creation of a network correct from the EPANET point of view (exploiting the standard QGIS editing tools, like other plugins do, would not give such guarantee).

In QEPANET you fill find all the following features:
- a set of dedicated editing tools (in a dockable toolbar) facilitating the management of the hydraulic network. These tools allow the creation, modification and deletion of the network elements, and enforce the topological correctness of the network. In addition, there are a set of nifty shortcuts to set the attributes of the network elements (e.g.: pipe
diameter and pipe material);
- the option of using a raster DTM to easily extract the elevation of the network nodes;
- the ability to draw the network elements in the order you prefer: as it automatically adds junctions at the end of newly created pipes (to avoid wrong commands to the EPANET software), there is no need to draw all the
junctions before drawing the links;
- support for 3D pipe lengths: it takes into account the elevation profile to automatically calculate the actual pipe length;
- easy setting of the maximum pipe length for construction purposes: you choose your pipe length from the manufacturer’s datasheet and QEPANET automatically inserts the vertices along the pipe at the appropriate distances;
- a graphical section editor to define and adjust the position of the pipe in relation to the ground. This is useful to set the excavation depth of the pipe;
- easy definition of the pipe properties such as material and roughness. It is for instance possible to choose the material and the plugin presents a range of realistic roughness values to choose from. The properties are managed by the plugin GUI, so that there are internal control on their consistency (there is support for IS and imperial units);
- a tool to edit the curves used to define pumps behaviour;
- a tool to edit the patterns used to define junctions behaviour;
- a series of tools to analyse the simulation results, that include thematic mapping of the network and graphs of the modelled entities along time.

Find tutorials and documentation in this Google Drive folder: https://goo.gl/cq3XNH

The project activities are made possible by the Autonomous Province of Bozen funding "AI_ALPEN Project, drinking water supply in alpine region, (CUP: B26J16000300003)" and by the Province of Trento funding "PAT AI APRIE public water resources management"
A gridded database of the modern distributions of climate, woody plant taxa, and ecoregions for the continental United States and Canada

Authors: 
Robert S. Thompson (1), Katherine H. Anderson (2), Richard T. Pelltier (1), Laura E. Strickland (1), Sarah L. Shafer (3), Patrick J. Bartlein (4)

(1) Geosciences and Environmental Change Science Center, U.S. Geological Survey, Denver, Colorado, USA
(2) Institute of Arctic and Alpine Research, University of Colorado, Boulder, Colorado, USA
(3) Geosciences and Environmental Change Science Center, U.S. Geological Survey, Corvallis, Oregon, USA
(4) Department of Geography, University of Oregon, Eugene, Oregon, USA

Contacts:  Robert Thompson (e-mail: rthompson@usgs.gov), Richard Pelltier (rtpelltier@usgs.gov)

Date: 25 April 2023


----------
Summary
----------
On the continental scale, climate is an important determinant of the distributions of plant taxa and ecoregions.  To quantify and depict the relations between specific climate variables and these distributions, we placed modern climate and plant taxa distribution data on an approximately 25-kilometer (km) equal-area grid with 27,984 points that cover Canada and the continental United States (Thompson and others, 2015).  The gridded climatic data include annual and monthly temperature and precipitation, as well as bioclimatic variables (growing degree days, mean temperatures of the coldest and warmest months, and a moisture index) based on 1961-1990 30-year mean values from the University of East Anglia (UK) Climatic Research Unit (CRU) CL 2.0 dataset (New and others, 2002), and absolute minimum and maximum temperatures for 1951-1980 interpolated from climate-station data (WeatherDisc Associates, 1989).  As described below, these data were used to produce portions of the "Atlas of relations between climatic parameters and distributions of important trees and shrubs in North America" (hereafter referred to as "the Atlas"; Thompson and others, 1999a, 1999b, 2000, 2006, 2007, 2012a, 2015).

Evolution of the Atlas Over the 16 Years Between Volumes A & B and G:
The Atlas evolved through time as technology improved and our knowledge expanded.  The climate data employed in the first five Atlas volumes were replaced by more standard and better documented data in the last two volumes (Volumes F and G; Thompson and others, 2012a, 2015).  Similarly, the plant distribution data used in Volumes A through D (Thompson and others, 1999a, 1999b, 2000, 2006) were improved for the latter volumes.  However, the digitized ecoregion boundaries used in Volume E (Thompson and others, 2007) remain unchanged.  Also, as we and others used the data in Atlas Volumes A through E, we came to realize that the plant distribution and climate data for areas south of the US-Mexico border were not of sufficient quality or resolution for our needs and these data are not included in this data release.

The data in this data release are provided in comma-separated values (.csv) files.  We also provide netCDF (.nc) files containing the climate and bioclimatic data, grouped taxa and species presence-absence data, and ecoregion assignment data for each grid point (but not the country, state, province, and county assignment data for each grid point, which are available in the .csv files).  The netCDF files contain updated Albers conical equal-area projection details and more precise grid-point locations.  When the original approximately 25-km equal-area grid was created (ca. 1990), it was designed to be registered with existing data sets, and only 3 decimal places were recorded for the grid-point latitude and longitude values (these original 3-decimal place latitude and longitude values are in the .csv files).  In addition, the Albers conical equal-area projection used for the grid was modified to match projection irregularities of the U.S. Forest Service atlases (e.g., Little, 1971, 1976, 1977) from which plant taxa distribution data were digitized.

For the netCDF files, we have updated the Albers conical equal-area projection parameters and recalculated the grid-point latitudes and longitudes to 6 decimal places.  The additional precision in the location data produces maximum differences between the 6-decimal place and the original 3-decimal place values of up to 0.00266 degrees longitude (approximately 143.8 m along the projection x-axis of the grid) and up to 0.00123 degrees latitude (approximately 84.2 m along the projection y-axis of the grid).  The maximum straight-line distance between a three-decimal-point and six-decimal-point grid-point location is 144.2 m.  Note that we have not regridded the elevation, climate, grouped taxa and species presence-absence data, or ecoregion data to the locations defined by the new 6-decimal place latitude and longitude data.  For example, the climate data described in the Atlas publications were interpolated to the grid-point locations defined by the original 3-decimal place latitude and longitude values.  Interpolating the data to the 6-decimal place latitude and longitude values would in many cases not result in changes to the reported values and for other grid points the changes would be small and insignificant.  Similarly, if the digitized Little (1971, 1976, 1977) taxa distribution maps were regridded using the 6-decimal place latitude and longitude values, the changes to the gridded distributions would be minor, with a small number of grid points along the edge of a taxa's digitized distribution potentially changing value from taxa "present" to taxa "absent" (or vice versa).  These changes should be considered within the spatial margin of error for the taxa distributions, which are based on hand-drawn maps with the distributions evidently generalized, or represented by a small, filled circle, and these distributions were subsequently hand digitized.  Users wanting to use data that exactly match the data in the Atlas volumes should use the 3-decimal place latitude and longitude data provided in the .csv files in this data release to represent the center point of each grid cell.  Users for whom an offset of up to 144.2 m from the original grid-point location is acceptable (e.g., users investigating continental-scale questions) or who want to easily visualize the data may want to use the data associated with the 6-decimal place latitude and longitude values in the netCDF files.

The variable names in the netCDF files generally match those in the data release .csv files, except where the .csv file variable name contains a forward slash, colon, period, or comma (i.e., "/", ":", ".", or ",").  In the netCDF file variable short names, the forward slashes are replaced with an underscore symbol (i.e., "_") and the colons, periods, and commas are deleted.  In the netCDF file variable long names, the punctuation in the name matches that in the .csv file variable names.  The "country", "state, province, or territory", and "county" data in the .csv files are not included in the netCDF files.


DATA INCLUDED IN THIS RELEASE
Below we provide a summary of the data included in this data release.  The individual variables included in the data release are listed in the accompanying metadata and data dictionary files.

1. Geographic scope
The gridded data cover an area that we labelled as "CANUSA", which includes Canada and the USA (excluding Hawaii, Puerto Rico, and other oceanic islands).  Note that the maps displayed in the Atlas volumes are cropped at their northern edge and do not display the full northern extent of the data included in this data release.

2. Elevation
The elevation data were regridded from the ETOPO5 data set (National Geophysical Data Center, 1993).  There were 35 coastal grid points in our CANUSA study area grid for which the regridded elevations were below sea level and these grid points were assigned missing elevation values (i.e., elevation = 9999).  The grid points with missing elevation values occur in five coastal areas: (1) near San Diego (California, USA; 1 grid point), (2) Vancouver Island (British Columbia, Canada) and the Olympic Peninsula (Washington, USA; 2 grid points), (3) the Haida Gwaii (formerly Queen Charlotte Islands, British Columbia, Canada) and southeast Alaska (USA, 9 grid points), (4) the Canadian Arctic Archipelago (22 grid points), and (5) Newfoundland (Canada; 1 grid point).

3. Climate
The gridded climatic data provided here are based on the 1961-1990 30-year mean values from the University of East Anglia (UK) Climatic Research Unit (CRU) CL 2.0 dataset (New and others, 2002), and include annual and monthly temperature and precipitation.  The CRU CL 2.0 data were interpolated onto the approximately 25-km grid using geographically-weighted regression, incorporating local lapse-rate estimation and correction.  Additional bioclimatic variables (growing degree days on a 5 degrees Celsius base, mean temperatures of the coldest and warmest months, and a moisture index calculated as actual evapotranspiration divided by potential evapotranspiration) were calculated using the interpolated CRU CL 2.0 data.  Also included are absolute minimum and maximum temperatures for 1951-1980 interpolated in a similar fashion from climate-station data (WeatherDisc Associates, 1989).  These climate and bioclimate data were used in Atlas volumes F and G (see Thompson and others, 2015, for a description of the methods used to create the gridded climate data).  Note that for grid points with missing elevation values (i.e., elevation values equal to 9999), climate data were created using an elevation value of -120 meters.  Users may want to exclude these climate data from their analyses (see the Usage Notes section below).

4. Plant distributions
The gridded plant distribution data align with Atlas volume G (Thompson and others, 2015).  Plant distribution data on the grid include 690 species, as well as 67 groups of related species and genera, and are based on U.S. Forest Service atlases (e.g., Little, 1971, 1976, 1977), regional atlases (e.g., Benson and Darrow, 1981), and new maps based on information available from herbaria and other online and published sources (for a list of sources, see Tables 3 and 4 in Thompson and others, 2015).  See the "Notes" column in Table 1 (https://pubs.usgs.gov/pp/p1650-g/table1.html) and Table 2 (https://pubs.usgs.gov/pp/p1650-g/table2.html) in Thompson and others (2015) for important details regarding the species and grouped taxa distributions.

5. Ecoregions
The ecoregion gridded data are the same as in Atlas volumes D and E (Thompson and others, 2006, 2007), and include three different systems, Bailey's ecoregions (Bailey, 1997, 1998), WWF's ecoregions (Ricketts and others, 1999), and Kuchler's potential natural vegetation regions (Kuchler, 1985), that are each based on distinctive approaches to categorizing ecoregions.  For the Bailey and WWF ecoregions for North America and the Kuchler potential natural vegetation regions for the contiguous United States (i.e., the lower 48 states), data are provided for the Level I, Level II, and Level III ecoregion classification of each grid point.  Level I ecoregions are the broadest ecoregion categories and generally cover relatively large areas (e.g., western forests).  Level II ecoregions are subregions of the Level I ecoregions and are more specifically defined (e.g., needleleaf forests).  Level III ecoregions are subregions of the Level II ecoregions (e.g., Great Basin pine forest [Pinus]) and generally cover relatively small areas.  For the Kuchler potential natural vegetation regions in Alaska, Kuchler (1985) did not include Level I and Level II regions in his classification and so only Level III Kuchler regions for Alaska are included in this data release.  Ecoregion and potential natural vegetation region names in this data release generally follow those used in Thompson and others (2006, 2007).

6. Estimation of climate from vegetation inventories
As described in Atlas volume F (Thompson and others, 2012a) and Thompson and others (2012b), vegetation inventories (plant taxa present in a vegetation assemblage at a given site) can be used to estimate climatic parameters based on the identification of the range of a given parameter where all taxa in an assemblage overlap (i.e., the "mutual climatic range"; MCR).  For the reconstruction of past climates from fossil or subfossil plant assemblages, we include matrices of 32 climatic and bioclimatic parameters versus occurrences or nonoccurrences for the same 690 species and 67 groups of related species and genera.  See the Methods section of volume F for more details (https://pubs.usgs.gov/pp/p1650-f/Methods.html; https://pubs.usgs.gov/pp/p1650-f/DataTables.html).


USAGE NOTES

Taxa Distributions
Important additional notes for the taxa distributions in this data release are provided in Tables 1 and 2 of Thompson and others (2015; https://pubs.usgs.gov/pp/p1650-g/table1.html and https://pubs.usgs.gov/pp/p1650-g/table2.html).  We strongly recommend that researchers review these tables before using the data in this data release.  The tables contain notes about the original taxa distribution data sources we used and how those sources were interpreted.  

The taxa names used in this data release match those used in the original data sources from which we obtained the taxa distribution data.  For many taxa, the currently accepted scientific name is different from that used in the original data sources and in this data release.  Table 1 of Thompson and others (2015; https://pubs.usgs.gov/pp/p1650-g/table1.html) lists each taxa name used in this data release along with its currently (ca. 2015) accepted scientific taxa name.

The distribution data in this data release may not encompass the entire range of a taxa.  Distribution data are not complete for taxa with distributions that extend south of the southern USA border (i.e., beyond the extent of our North America grid).  Similarly, for taxa with circumpolar distributions (e.g., Juniperus communis), this data release only includes data for the portions of the taxa’s ranges that occur in North America.


Climate Data 
For the 35 grid points with missing elevation values (i.e., elevation values equal to 9999), climate data were created using a grid point elevation of -120 meters (i.e., 120 meters below sea level).  These climate data do not represent the climate of the land surface and researchers may want to exclude these data from their analyses.


Using Panoply
Panoply (https://www.giss.nasa.gov/tools/panoply/) is publicly available software that can be used to view the data in the Atlas netCDF files.


ERRATUM
The distribution of California torreya (Torreya californica) in this data release and in Thompson and others (2015) contains an erroneous grid point in Nova Scotia (Canada).  This error also affects the data for taxa groups Cupressaceae/Taxaceae and Cupressaceae/Taxaceae West, which include Torreya californica.  


----------
REQUIREMENTS
----------
This data release includes netCDF files (Unidata 2011).  NetCDF software is available from http://www.unidata.ucar.edu/downloads/netcdf/index.jsp.  A number of software packages are available for viewing netCDF files (e.g., Panoply, available at https://www.giss.nasa.gov/tools/panoply/). 


----------
HOW TO CITE THESE DATA
----------
Thompson, R.S., Anderson, K.H., Pelltier, R.T., Strickland, L.E., Shafer, S.L., and Bartlein, P.J., 2023, A gridded database of the modern distributions of climate, woody plant taxa, and ecoregions for the continental United States and Canada: U.S. Geological Survey data release, https://doi.org/10.5066/P9FPD80E.


----------
DISCLAIMER
----------
Although these data have been processed successfully on a computer system at the U.S. Geological Survey (USGS), no warranty expressed or implied is made regarding the display or utility of the data for other purposes, nor on all computer systems, nor shall the act of distribution constitute any such warranty.  The USGS or the U.S. Government shall not be held liable for improper or incorrect use of the data described and/or contained herein.  Although this information product, for the most part, is in the public domain, it also may contain copyrighted materials as noted in the text.  Permission to reproduce copyrighted items must be secured from the copyright owner.  Any use of trade, firm, or product names is for descriptive purposes only and does not imply endorsement by the U.S. Government.


----------
REFERENCES
----------
Bailey, R.G., 1997. Map: Ecoregions of North America (rev.), scale 1:15,000,000. U.S. Department of Agriculture Forest Service, Washington, D.C.

Bailey, R.G., 1998. Ecoregions map of North America: Explanatory note. Miscellaneous Publication 1548. U.S. Department of Agriculture Forest Service, Washington, D.C.

Benson, L., and Darrow, R.A., 1981. Trees and shrubs of the southwestern deserts (3rd ed.). University of Arizona Press, 416 p.

Kuchler, A.W., 1985. Potential natural vegetation. National Atlas of the United States of America. U.S. Geological Survey. https://doi.org/10.3133/32574

Little, E.L., Jr., 1971. Atlas of United States trees, volume 1, Conifers and important hardwoods. U.S. Department of Agriculture Forest Service, Miscellaneous Publication 1146, Washington, D.C., 200 maps. https://doi.org/10.5962/bhl.title.130546

Little, E.L., Jr., 1976. Atlas of United States trees, volume 3, Minor western hardwoods. U.S. Department of Agriculture Forest Service, Miscellaneous Publication 1314, Washington, D.C., 210 maps. https://doi.org/10.5962/bhl.title.65782

Little, E.L., Jr., 1977. Atlas of United States trees, volume 4, Minor eastern hardwoods. U.S. Department of Agriculture Forest Service, Miscellaneous Publication 1342, Washington, D.C., 166 maps. https://doi.org/10.5962/bhl.title.65458

National Geophysical Data Center, 1993. National Geophysical Data Center, 5-minute gridded global relief data (ETOPO5), National Geophysical Data Center, NOAA. https://doi.org/10.7289/V5D798BF

New, M., Lister, D., Hulme, M., and Makin, I., 2002. A high-resolution data set of surface climate over global land areas. Climate Research 21, 1-25. https://doi.org/10.3354/cr021001

Ricketts, T.H., Dinerstein, E., Olson, D.M., Loucks, C.J., Eichbaum, W.M., DellaSala, D.A., Kavanagh, K.C., Hedao, P., Hurley, P.T., Carney, K.M., Abell, R.A., and Walters, S., 1999. Terrestrial ecoregions of North America: a conservation assessment. Island Press, Washington, D.C., 485 p.

Thompson, R.S., Anderson, K.H., and Bartlein, P.J., 1999a. Atlas of relations between climatic parameters and distributions of important trees and shrubs in North America -- Introduction and conifers. U.S. Geological Survey Professional Paper 1650-A, 269 p. https://doi.org/10.3133/pp1650AB (Online version: https://pubs.usgs.gov/pp/p1650-a/)

Thompson, R.S., Anderson, K.H., and Bartlein, P.J., 1999b. Atlas of relations between climatic parameters and distributions of important trees and shrubs in North America -- Hardwoods. U.S. Geological Survey Professional Paper 1650-B, 423 p. https://doi.org/10.3133/pp1650AB (Online version: https://pubs.usgs.gov/pp/p1650-b/)

Thompson, R.S., Anderson, K.H., Bartlein, P.J., and Smith, S.A., 2000. Atlas of relations between climatic parameters and distributions of important trees and shrubs in North America -- Additional conifers, hardwoods, and monocots. U.S. Geological Survey Professional Paper 1650-C, 386 p. https://doi.org/10.3133/pp1650C

Thompson, R.S., Anderson, K.H., Strickland, L.E., Shafer, S.L., Pelltier, R.T., and Bartlein, P.J., 2006. Atlas of relations between climatic parameters and distributions of important trees and shrubs in North America -- Alaska species and ecoregions. U.S. Geological Survey Professional Paper 1650-D. https://doi.org/10.3133/pp1650D (Online version: https://pubs.usgs.gov/pp/p1650-d/)

Thompson, R.S., Anderson, K.H., Pelltier, R.T., Shafer, S.L., and Bartlein, P.J., 2007. Atlas of relations between climatic parameters and distributions of important trees and shrubs in North America -- Ecoregions of North America. U.S. Geological Survey Professional Paper 1650-E. https://doi.org/10.3133/pp1650E (Online version: https://pubs.usgs.gov/pp/p1650-e/)

Thompson, R.S., Anderson, K.H., Pelltier, R.T., Strickland, L.E., Shafer, S.L., and Bartlein, P.J., 2012a. Atlas of relations between climatic parameters and distributions of important trees and shrubs in North America -- Modern data for climatic estimation from vegetation inventories. U.S. Geological Survey Professional Paper 1650-F, CD-ROM. https://doi.org/10.3133/pp1650F (Online version: https://pubs.usgs.gov/pp/p1650-f/)

Thompson, R.S., Anderson, K.H., Pelltier, R.T., Strickland, L.E., Bartlein, P.J., and Shafer, S.L., 2012b. Quantitative estimation of climatic parameters from vegetation data in North America by the mutual climatic range technique. Quaternary Science Reviews, v. 51, p. 18–39. https://doi.org/10.1016/j.quascirev.2012.07.003

Thompson, R.S., Anderson, K.H., Pelltier, R.T., Strickland, L.E., Shafer, S.L., Bartlein, P.J., and McFadden, A.K., 2015. Atlas of relations between climatic parameters and distributions of important trees and shrubs in North America -- Revisions for all taxa from the United States and Canada and new taxa from the western United States. U.S. Geological Survey Professional Paper 1650-G. https://doi.org/10.3133/pp1650G (Online version: https://pubs.usgs.gov/pp/p1650-g/)

Unidata, 2011. Network Common Data Form (netCDF) version 4.1.3 [software]. UCAR/Unidata, Boulder, Colorado. https://doi.org/10.5065/D6H70CW6

WeatherDisc Associates, 1989. World WeatherDisc, version 1.0. Seattle, Washington, WeatherDisc Associates, CD-ROM.


importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var known = true;
for (var i=0; i<4; i++) known = known && PVUtil.getTimeInMilliseconds(pvs[i]) > 0;
widget.setPropertyValue("text", !known ? "No identity" : PVUtil.getLong(pvs[0])+"."+PVUtil.getLong(pvs[1])+"."+PVUtil.getLong(pvs[2])+(PVUtil.getLong(pvs[3]) ? " dirty" : " clean")+(PVUtil.getSeverity(pvs[0]) < 0 ? " · expired" : ""));

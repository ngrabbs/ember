importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var known = PVUtil.getTimeInMilliseconds(pvs[0]) > 0;
var current = known && PVUtil.getSeverity(pvs[0]) >= 0;
widget.setPropertyValue("text", !current ? "—" : PVUtil.getLong(pvs[0]) === 1 ? (PVUtil.getLong(pvs[1])/1000).toFixed(1)+" s" : "Never seen");

importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var valid = PVUtil.getSeverity(pvs[0]) >= 0 && PVUtil.getSeverity(pvs[1]) >= 0 && PVUtil.getLong(pvs[1]) === 1;
var v = PVUtil.getDouble(pvs[0]);
widget.setPropertyValue("text", valid && v > -2147483 ? v.toFixed(3) + " " + PVUtil.getUnits(pvs[0]) : "Unavailable");

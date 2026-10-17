importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var time = PVUtil.getTimeInMilliseconds(pvs[0]);
var valid = time > 0 && PVUtil.getSeverity(pvs[0]) >= 0;
var text = valid ? PVUtil.getString(pvs[0]) : "—";
var unit = PVUtil.getUnits(pvs[0]);
widget.setPropertyValue("text", text + (valid && unit ? " " + unit : ""));

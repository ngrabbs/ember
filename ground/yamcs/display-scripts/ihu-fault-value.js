importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var name = PVUtil.getString(pvs[0]);
var present = PVUtil.getTimeInMilliseconds(pvs[0]) > 0 &&
    PVUtil.getSeverity(pvs[0]) >= 0 && name && name !== "EMPTY";
var value = pvs.length > 1 ? pvs[1] : pvs[0];
widget.setPropertyValue("text", present ? PVUtil.getString(value) : "");

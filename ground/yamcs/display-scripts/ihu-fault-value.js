importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var present = PVUtil.getTimeInMilliseconds(pvs[0]) > 0 &&
    PVUtil.getSeverity(pvs[0]) >= 0 && PVUtil.getDouble(pvs[0]) > 0;
var value = pvs.length > 1 ? pvs[1] : pvs[0];
widget.setPropertyValue("text", present ? PVUtil.getString(value) : "");

importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var valid = PVUtil.getTimeInMilliseconds(pvs[0]) > 0 && PVUtil.getSeverity(pvs[0]) >= 0;
widget.setPropertyValue("text", !valid ? "—" : PVUtil.getLong(pvs[0]) === 1 ? "Yes" : "No");

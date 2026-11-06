importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var pv = pvs[0];
var unit = PVUtil.getUnits(pv);
var value = PVUtil.getDouble(pv);
var valid = PVUtil.getTimeInMilliseconds(pv) > 0 && PVUtil.getSeverity(pv) >= 0 &&
    value > (unit === "m" ? -2147483 : -214);
widget.setPropertyValue("text", valid ? value.toFixed(unit === "m" ? 1 : 6) + " " + unit : "Unavailable");

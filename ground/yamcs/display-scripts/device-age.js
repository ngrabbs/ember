importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
widget.setPropertyValue("text", PVUtil.getLong(pvs[0]) === 1 ? String(PVUtil.getLong(pvs[1])) : "Never seen");

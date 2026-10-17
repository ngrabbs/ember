importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
widget.setPropertyValue("text", PVUtil.getLong(pvs[0])+"."+PVUtil.getLong(pvs[1])+"."+PVUtil.getLong(pvs[2])+(PVUtil.getLong(pvs[3]) ? " (dirty build)" : " (clean build)"));

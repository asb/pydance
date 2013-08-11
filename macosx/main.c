/* main.c */

#include <Carbon/Carbon.h>

#include <unistd.h>

#define PYTHON_BIN "/Library/Frameworks/Python.framework/Versions/2.3/bin/python"

int main(int argc, char *argv[])
{
	CFBundleRef mainBundle;
	CFURLRef resourcesURL;
	char buf[4096];
	
	char *const args[] = {
		"PyDDR",
		"./pyddr.py",
		NULL
	};
	
	mainBundle = CFBundleGetMainBundle();
	resourcesURL = CFBundleCopyResourcesDirectoryURL(mainBundle);
	CFURLGetFileSystemRepresentation(resourcesURL, true, buf, 4096);
	CFRelease(resourcesURL);
	
	chdir(buf);
	
	return execv(PYTHON_BIN, args);
}

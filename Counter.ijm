open(getArgument());
run("8-bit");
run("Median...", "radius=3");
setAutoThreshold("Otsu");
run("Threshold...");
run("Convert to Mask");
run("Invert");
// If nuclei are clumped, try uncommenting the next line:
 run("Watershed");
run("Analyze Particles...", "size=600-5000 circularity=0.00-1.00 show=Outlines display clear summarize");
count = nResults;
print("Count: " + count);
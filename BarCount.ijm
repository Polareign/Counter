run("Clear Results");

original = getImageID();
selectImage(original);
run("Duplicate...", "title=working");
working = getImageID();

selectImage(working);
if (bitDepth() != 24) run("RGB Color");

width = getWidth();
height = getHeight();

run("Split Channels");
greenTitle = "working (green)";
selectWindow(greenTitle);
run("Duplicate...", "title=green_lines");
setThreshold(100, 255);
run("Make Binary");
run("Invert");

selectImage(original);
run("Duplicate...", "title=with_black_lines");
setForegroundColor(0, 0, 0);
setLineWidth(2);

horizontal_lines = 7;
vertical_lines = 9;
horizontal_spacing = height / (horizontal_lines + 1);
vertical_spacing = width / (vertical_lines + 1);

for (i = 1; i <= horizontal_lines; i++) {
    y = i * horizontal_spacing;
    makeLine(0, y, width, y);
    run("Draw", "slice");
}

for (i = 1; i <= vertical_lines; i++) {
    x = i * vertical_spacing;
    makeLine(x, 0, x, height);
    run("Draw", "slice");
}

run("Duplicate...", "title=with_black_lines_mask");
selectWindow("with_black_lines_mask");
run("Split Channels");
selectWindow("with_black_lines_mask (green)");
run("Duplicate...", "title=black_lines");
setThreshold(0, 50);
run("Make Binary");

imageCalculator("AND create", "green_lines", "black_lines");
rename("intersections");

run("Median...", "radius=1");
run("Analyze Particles...", "size=5-500 circularity=0.00-1.00 show=Nothing clear");
intersection_count = nResults;

ppi = 96;
pixels_per_foot = ppi * 12;
line_length_px = (horizontal_lines * width) + (vertical_lines * height);
line_length_ft = line_length_px / pixels_per_foot;

print("Count: " + intersection_count / line_length_ft + " count/ft");

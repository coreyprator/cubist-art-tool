import cv2
import numpy as np
import os

# Load image
image = cv2.imread("your_input_image.jpg")  # Replace with your actual image filename

# Apply posterization
Z = image.reshape((-1, 3))
Z = np.float32(Z)

# Define criteria and apply kmeans
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
K = 8  # Number of color clusters
_, labels, centers = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

centers = np.uint8(centers)
res = centers[labels.flatten()]
posterized = res.reshape((image.shape))

# Save to same directory as script
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, "posterized_result.jpg")
cv2.imwrite(output_path, posterized)

# Optional: show image
cv2.imshow("Posterized", posterized)
cv2.waitKey(0)
cv2.destroyAllWindows()

## 1. 3DGS (3D Gaussian Splatting)
A method for representing and rendering 3D scenes. Instead of a mesh or neural implicit field, the scene is modeled as a large collection of 3D Gaussians — each with a position, orientation/shape (covariance), opacity, and color. These are "splatted" (projected) onto a 2D image plane to render a view very quickly, which is why 3DGS has become popular for real-time, photorealistic novel-view synthesis.

## 2. Language-Embedded 3DGS
A plain 3DGS scene only knows about geometry and color — it has no idea what a "chair" or "mug" is. To make the scene queryable with natural language, researchers attach an additional semantic feature vector to each Gaussian (often derived from CLIP, the vision-language model that maps images and text into a shared embedding space). Once every Gaussian carries such a feature, you can type a text query like "the red backpack," embed it with CLIP, and find which Gaussians in the 3D scene have the closest matching features — enabling open-vocabulary 3D segmentation, retrieval, and editing.

## 3. Multi-View Semantic Consistency (the core problem being solved)
The language features aren't observed in 3D directly — they're extracted from 2D training images (using tools like SAM for segmentation and CLIP for semantics) and then "lifted" into the 3D Gaussians. The problem: when you run these 2D models independently on each camera view, the same physical object can get:

different segmentation boundaries from different angles,
different instance IDs,
slightly different CLIP embeddings (due to occlusion, cropping, lighting, or viewing angle).

This is called multi-view inconsistency, and it's a major source of noisy, blurry, or contradictory semantics once you try to fuse everything into one 3D representation. "Multi-view semantic consistency" is the property (and goal) of making sure the same 3D object ends up with one coherent semantic identity/feature regardless of which training view it's seen from.

## 4. Video Mask Propagation (the proposed mechanism for achieving that consistency)
Rather than segmenting each view independently and then trying to reconcile the differences afterward, this approach treats the sequence of camera views as if it were a video (which is often literally true — many 3DGS scenes are captured by walking a camera around a room). It then uses video object segmentation/tracking models (e.g., SAM2, or similar mask-propagation techniques) to:

generate or select a mask for an object in one (or a few) reference frames, and
propagate/track that same mask forward and backward through the rest of the frames, preserving a single consistent object identity across all of them.

Because the mask's identity is now tracked rather than independently re-detected each time, the language/semantic features attached to that object across all views are consistent by construction, rather than needing post-hoc clustering or voting to fix disagreements.

## Putting it all together

The title describes a method for building 3D Gaussian Splatting scenes with embedded language/semantic features, where the key contribution is ensuring those semantic features agree across all viewpoints — achieved specifically by using video-style mask propagation/tracking (rather than independent per-view segmentation) to maintain a consistent object identity throughout the training views before fusing the corresponding language features into the 3D Gaussians. The end goal is a 3D scene you can query with open-ended text ("find the mug," "select the sofa") where the resulting 3D segmentation is clean and object-coherent rather than fragmented or noisy.
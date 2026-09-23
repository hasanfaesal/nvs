Multi-View Semantic Consistency in Language-Embedded 3DGS with Video Mask Propagation



Project Proposal


  







Supervisor
Mr. Abdul Rahman




Submitted by  

Hasan Faisal
01-136232-017
Zulqarnain Munir
01-136232-050






Department of Computer Science,
Bahria University, Islamabad.

10th September 2026

1. Introduction
Recent progress in neural scene representations, particularly 3D Gaussian Splatting (3DGS) [1], enables real-time photorealistic view synthesis on standard graphic cards. Although standard 3DGS reconstructs scene appearance with high fidelity from multi-view photographs, it represents the physical world strictly as an unstructured collection of millions of colored ellipsoids. The model contains no intrinsic concept of object boundaries, parts, or semantic categories. A user can render a room from novel viewpoints, but the underlying representation cannot isolate a specific piece of furniture from its surrounding floor or wall.

In parallel, 2D vision-language foundation models, such as the Segment Anything Model (SAM 2) [2] and Contrastive Language-Image Pre-training (CLIP) [3], provide open-vocabulary segmentation on isolated images. However, lifting 2D segmentations into a consistent 3D representation presents a persistent challenge. Generating 2D masks on independent video frames produces noisy, viewpoint-dependent supervision because single-image segmenters lack temporal memory. As the camera moves around an object, masks fluctuate, omit parts, or merge adjacent surfaces, leading to cross-view label disagreement.

This project investigates whether video mask propagation can mitigate these multi-view inconsistencies. The proposed system uses static indoor environments through standard phone video, reconstructs a 3D Gaussian radiance field using camera poses from Structure-from-Motion [4], and optimizes scale-conditioned 3D Gaussian affinity features [5] using temporally tracked 2D masks from SAM 2 [2]. By connecting learned 3D affinity descriptors to visual CLIP embeddings [3], the system enables users to locate, isolate and inspect physical objects using natural language queries or direct mouse clicks inside a web browser viewer.
2. Objective
To develop a prototype system that reconstructs static indoor scenes from video into 3D Gaussian radiance fields, trains scale-conditioned 3D semantic affinity features supervised by temporally tracked SAM 2 masks and provides interactive text and click-based object selection inside a web browser interface.
3. Problem Description
Interactive 3D computing requires systems that recognize distinct objects within a physical space, rather than merely synthesizing surface color. Standard 3D Gaussian Splatting produces unstructured collections of millions of ellipsoids. The representation lacks object awareness, which prevents automated editing, semantic querying, and spatial reasoning.

While 2D vision foundation models identify objects accurately in static images, applying them across multi-view video introduces severe cross-view inconsistencies. Independent per-frame segmentations fluctuate under camera motion, partial occlusion, and changing illumination. A chair cushion may be grouped with its frame in one view, excluded in another, or merged with the floor. When these inconsistent 2D masks supervise 3D feature fields, contradictory gradients degrade the learned 3D representation, causing noisy selections and boundary leakage across viewpoints.
4. Methodology
The proposed methodology follows a modular six-stage pipeline that transitions from raw mobile video recording to real-time client-side interaction:
1. Structure-from-Motion and Camera Pose Estimation: A monocular phone video recording a static scene is downsampled into 60 to 120 sharp, overlapping frames. COLMAP [4] extracts local visual descriptors, matches correspondences across frames, and estimates camera intrinsics, camera extrinsics, and an initial sparse 3D point cloud.
2. Base 3D Gaussian Splatting Reconstruction: The scene is parameterized into 3D Gaussians initialized from the sparse point cloud. Through GPU-accelerated rasterization, Gaussian positions, rotations, scales, opacities, and spherical harmonic colors are optimized against captured training views until convergence [1]. Ten to twenty percent of camera views are held out for evaluation.
3. Multi-View 2D Pseudo-Labeling with SAM 2: Instead of segmenting each frame independently, key frames are prompted across the sequence. The official SAM 2 video predictor [2] propagates object masks bidirectionally through time, enforcing persistent temporal track IDs and reducing cross-view mask boundary disagreement.
4. Physical Scale Estimation and CLIP Vision Extraction: For each 2D mask, corresponding depth maps rendered from the trained 3DGS model lift 2D pixels into 3D camera coordinates. The physical bounding radius is computed to establish a scale-conditioned hierarchy distinguishing fine parts from whole objects. Concurrently, masked visual crops are processed by a frozen CLIP ViT [3] image encoder to produce normalized semantic visual vectors.
5. Contrastive Gaussian Affinity Field Optimization: Building on the SAGA architecture [5], a trainable 32-dimensional affinity vector and a scale-gating multilayer perceptron are attached to each 3D Gaussian, while RGB geometry remains frozen. Ray compositing renders 2D feature maps from 3D affinity vectors. Contrastive pixel-pair loss pulls features of co-masked Gaussians together and pushes unmasked background features apart, integrating multi-view constraints into a persistent 3D descriptor field.
·   6. Open-Vocabulary Querying and Web Viewer Inference: For text queries, the user input is encoded by CLIP and matched via cosine similarity and voting against candidate 3D target clusters. For click queries, the selected pixel affinity feature is retrieved and compared directly against scale-gated Gaussian features. Target Gaussians are highlighted, isolated, or recolored inside an interactive Three.js and GaussianSplats3D web application running on the client browser.
System Architecture: The architecture separates compute-intensive offline processing from lightweight online inference. Offline tasks (COLMAP, 3DGS training, SAM 2 propagation, and SAGA contrastive optimization) run in a pinned PyTorch and CUDA backend. Online services use a FastAPI server that manages CLIP text encoding, spatial index caching, and threshold filtering. The frontend is built in Next.js and Three.js, streaming compact Gaussian selection bitsets to the client viewer.
Software Process Model: The project adopts an iterative, milestone-driven development model. Development proceeds through sequential functional iterations: literature review and scope definition, baseline environment reproduction, dataset collection, mask adapter implementation, contrastive model training, backend API service construction, and frontend client integration. Verification gates at defense checkpoints ensure memory stability and rendering performance.
5. Project Scope
In-Scope Aspects:
·   Reconstruction and Grounding: Reconstruction of one to two static indoor environments (such as a desk, tabletop, or room corner) captured via smartphone video.
·   Supervision Adaptation: Integration of temporally propagated SAM 2 video masks as supervision for SAGA affinity field learning.
·   Interactive Modalities: Support for open-vocabulary natural language text prompts and direct mouse-click object selection.
·   Client-Side Manipulation: Interactive 3D manipulation modes in the browser prototype, including object isolation, visual transparency, and Gaussian recoloring.
·   Empirical Evaluation: A focused experimental comparison between independent SAM and SAM 2 supervision on a small number of scenes under matched training settings, measuring Mean IoU on held-out views and visual consistency.


Out-of-Scope Aspects:
·   Dynamic Scenes: Reconstruction of scenes containing moving people, dynamic objects, or changing environmental illumination.
·   Generative Inpainting: Hallucinating or generating occluded background geometry when an object is removed; hidden regions simply reveal underlying empty space.
· Real-Time Mobile SLAM: Live on-device camera tracking or instantaneous mobile model training; scene preprocessing remains an offline GPU workflow.
·   Foundation Model Pretraining: Training SAM 2 or CLIP backbones from scratch; foundation models are utilized strictly in frozen inference mode.
·   Complex Relational Parsing: High-level spatial prepositional reasoning (such as 'the item owned by the student near the door') without explicit visual grounding.
·   Production Web Deployment: Multi-user concurrency, distributed cloud scaling, and user authentication are excluded in favor of a local prototype demonstration.
6. Feasibility Study
The project is structured for completion within the academic timeline using available institutional hardware, incorporating explicit fallback options if technical difficulties arise.
Risks Involved and Mitigation Strategies:
1. Structure-from-Motion Failure: Low-texture surfaces or motion blur can cause COLMAP reconstruction to fail on custom phone recordings. 
Mitigation: Standardized capture protocols using diffused lighting, high surface texture, slow orbital paths, 1080p capture resolution, and automated frame sharpness filtering. Fallback: If custom capture encounters persistent convergence issues, standard pre-processed public benchmarks (such as LERF) will serve as the primary evaluation scenes.
2. GPU Out-of-Memory Errors: Training 3DGS and contrastive affinity fields on high-resolution images can exceed VRAM limits.
 Mitigation: All pipelines use a strict downsampling factor of 8 during initial training, capping peak VRAM usage below 14 GB on a 16 GB NVIDIA RTX A4000 GPU.
3. Temporal Mask Drift: SAM 2 tracking can drift during severe occlusion or viewpoint shifts.
Mitigation: Keyframe prompt insertion at regular intervals across the video sequence resets object tracks and maintains identity consistency.
4. Web Client Latency: Transferring full scene geometries upon every query introduces network lag. 
Mitigation: The backend transmits compact 1-byte confidence arrays or selection bitsets, enabling client-side Three.js shaders to update colors and opacities in under 50 milliseconds.

Resource Requirements:
·   Compute Hardware: One workstation equipped with an NVIDIA RTX A4000 GPU (16 GB VRAM), 32 GB system RAM, and an 8-core CPU.
·   Capture Hardware: Standard smartphone camera recording 1080p video at 30 frames per second.
·   Software Environment: Ubuntu 22.04 LTS, CUDA 11.8/12.1, Python 3.10, PyTorch 2.1, COLMAP 3.8, Node.js 20, and modern WebGL-compliant web browsers.
7. Solution Application Areas
The proposed system provides functional utility across several technical and industrial domains:
·   Embodied AI and Robot Manipulation: Autonomous service robots require 3D spatial object localization from natural language instructions (such as 'pick up the yellow mug') to compute collision-free grasping trajectories.
·   Digital Twins and Asset Inspection: Industrial facilities and data centers can capture physical rooms and allow engineers to search, tag, and inspect equipment inventory remotely through open-vocabulary text queries.
·   Architectural Visualization and Interior Design: Designers and clients can inspect photorealistic building scans, isolate specific furniture pieces, inspect dimensions, and test color variations interactively in a browser without CAD modeling.
·  Virtual Reality and Interactive E-Commerce: Online retail environments can present real-world physical showroom scans where customers orbit items and interact with individual products using natural language.
8. Tools/Technology
The system integrates the following hardware, software libraries, and frameworks:
Category	Tool / Library	Role and Justification
Programming Languages	Python 3.10, TypeScript, GLSL	Backend machine learning, frontend web logic, and custom WebGL shaders.
Machine Learning	PyTorch 2.1, CUDA Toolkit	GPU-accelerated tensor operations, gradient autograd, and CUDA kernels.
Pose Estimation	COLMAP 3.8	Sparse Structure-from-Motion and camera parameter reconstruction.
3D Representation	3D Gaussian Splatting	Fast differentiable rasterization and photorealistic scene synthesis.
Semantic Segmentation	Segment Anything 2 (SAM 2)	Bidirectional video object mask propagation and tracking.
Language Grounding	OpenCLIP (ViT-B/16)	Joint multimodal text and image region semantic embedding.
Affinity Learning	SAGA (Segment Any 3D Gaussians)	Scale-conditioned contrastive affinity field optimization.
Backend Web API	FastAPI, Uvicorn, SQLite	High-throughput asynchronous query handling and metadata caching.
Frontend & Viewer	Next.js, React, Three.js	Interactive client-side orbit controls, splat rendering, and UI.
9. Expertise of the Team Members
Neither team member has formally studied Computer Graphics or Photogrammetry as a designated university course; both members are actively self-studying 3D coordinate geometry, projective camera transformations, and GPU rasterization pipelines through standard technical literature and open-source implementations.
The team has completed comprehensive foundational coursework in Artificial Intelligence, Computer Science and Applied Mathematics at Bahria University, providing the required background for this project. Specifically, the team's coursework includes:
·   Computer Vision and Deep Learning: Computer Vision (AIC 304 / AIL 304) and Deep Learning (AIC 401) provide practical experience in convolutional architectures, vision transformers, feature extraction, and camera geometry.
·  Machine Learning and AI Fundamentals: Machine Learning (AIC 301 / AIL 301) and Artificial Intelligence (AIC 201 / AIL 201) establish foundational knowledge in gradient-based optimization, loss formulation, and contrastive representation learning.
·  Mathematical Foundations: Linear Algebra (GSC 121) and Multivariable Calculus (GSC 211) provide essential grounding for 3D rotation quaternions, affine projections, and backpropagation in differentiable rendering.
·  High-Performance Computing: Parallel and Distributed Computing (AIC 302 / AIL 302) equips the team with knowledge of CUDA execution models, memory management, and parallel GPU processing.
·   Natural Language Processing: Natural Language Processing (AIC 442 / AIL 442) covers vector embeddings, semantic spaces, and transformer-based tokenization required for CLIP text grounding.
·   Software Architecture and Algorithms: Data Structures and Algorithms (CSC 221 / CSC 321) and Software Engineering (SEN 220) support the design of efficient spatial lookup structures and modular client-server software.

10. Milestones
The project is structured across an 8-month timeline covering both the 7th and 8th academic semesters. The schedule groups complex development tasks into two-month blocks and aligns directly with the department milestone defenses:
Period / Month	Milestone Focus	Key Deliverables and Validation Criteria	Academic Checkpoint
Month 1 (Sep 2026)	Literature Review, Requirements and Scope Finalization	Complete literature study on 3DGS, foundation models, and multi-view lift methods; finalize objective criteria, dataset specifications, compute budget, and risk boundaries.	Proposal Presentation (Week 3)
Month 2 (Oct 2026)	Environment Setup and Baseline SAGA Reproduction	Build pinned CUDA and PyTorch environment on A4000 GPU; reproduce SAGA feature optimization on a single public benchmark scene; profile peak VRAM and execution runtime.	Initial Project Defense (Week 8)
Months 3-4 (Nov-Dec 2026)	Custom Data Collection and SAM 2 Mask Propagation Adapter	Capture one to two static indoor scenes; run COLMAP pose estimation and train base 3DGS models; implement bidirectional SAM 2 keyframe tracking adapter to export consistent 2D mask sequences.	Midterm Project Defense (Week 16)
Months 5-6 (Jan-Feb 2027)	Contrastive 3D Feature Training and Query API Service	Train scale-conditioned 3D Gaussian affinity fields under matched baseline vs. SAM 2 supervision; develop backend FastAPI service for CLIP text encoding and spatial index matching.	8th Semester Core Development
Month 7 (Mar 2027)	Evaluation, Error Analysis and Web Viewer Prototype	Compute held-out Mean IoU and cross-view consistency metrics; analyze failure cases; integrate GaussianSplats3D web viewer prototype with highlight and isolate controls.	Pre-submission Review
Month 8 (Apr-May 2027)	Report Finalization, Open House and Project Defense	Complete final technical documentation, prepare demonstration backups, present system at university Open House, and defend project before examination committee.	Report (Week 13), Open House (Week 14), Final Defense (Week 15)
11. References
The proposal is grounded in the following foundational academic literature and technical documentation:
[1] Kerbl, B., Kopanas, G., Leimkuehler, T. and Drettakis, G., 2023. '3D Gaussian Splatting for Real-Time Radiance Field Rendering', ACM Transactions on Graphics, 42(4), pp. 139:1-139:14. doi:10.1145/3592433.
[2] Ravi, N., Gabeur, V., Hu, Y.T., Hu, R., Ryali, C., Ma, T., Khedr, H., Radle, R., Rolland, C., Gustafson, L., Mintun, E., Pan, J., Alwala, K.V., Carion, N., Wu, C.Y., Girshick, R., Dollar, P. and Feichtenhofer, C., 2024. 'SAM 2: Segment Anything in Images and Videos', arXiv preprint arXiv:2408.00714.
[3] Radford, A., Kim, J.W., Hallacy, C., Ramesh, A., Goh, G., Agarwal, S., Sastry, G., Askell, A., Mishkin, P., Clark, J., Krueger, G. and Sutskever, I., 2021. 'Learning Transferable Visual Models From Natural Language Supervision', International Conference on Machine Learning (ICML), PMLR 139, pp. 8748-8763.
[4] Schonberger, J.L. and Frahm, J.M., 2016. 'Structure-from-Motion Revisited', Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 4104-4113. doi:10.1109/CVPR.2016.445.
[5] Jiao, P., Chen, Z., Chen, J. and Shen, L., 2025. 'SAGA: Segment Any 3D Gaussians', Proceedings of the AAAI Conference on Artificial Intelligence (AAAI), 39, pp. 1-9. arXiv:2312.00860.
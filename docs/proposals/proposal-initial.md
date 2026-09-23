# Interactive Novel View Synthesis from Monocular Video

## Project Proposal

### Supervisor
Mr. Abdul Rahman

### Submitted by
Hasan Faisal (01-136232-017)  
Zulqarnain Munir (01-136232-050)

Department of Computer Science,  
Bahria University, Islamabad.  
10th September 2026

---

## 1. Introduction
Novel view synthesis generates photorealistic images of a physical space from camera angles that were never recorded during data collection. Historically, creating interactive 3D visualizations of real-world environments required specialized hardware, such as LiDAR scanners or multi-camera arrays, followed by complex polygon meshing pipelines. These approaches struggle with fine textures, specular highlights, and thin structures.

Recent developments in neural rendering allow users to capture scenes using a single moving camera, such as a handheld smartphone. Two paradigms currently dominate this area: Neural Radiance Fields (NeRF) [1] and 3D Gaussian Splatting (3DGS) [2]. 

NeRF optimizes a continuous volumetric representation parameterized by a multilayer perceptron [1]. While NeRF methods achieve high visual fidelity, their rendering process relies on ray marching. Querying a neural network hundreds of times per pixel creates high computational overhead, making real-time interactive rendering difficult on consumer-grade devices without powerful local GPUs or costly server streaming.

3D Gaussian Splatting provides an alternative by representing scenes with millions of 3D Gaussians [2]. These explicit primitives are rendered through GPU-accelerated rasterization rather than volumetric ray integration. This formulation enables real-time frame rates on standard graphics hardware while maintaining visual quality comparable to neural volumetric methods.

This project examines the practical trade-offs of these methods when applied to casual monocular video captured on mobile phones. The proposed system processes handheld video through Structure-from-Motion, compares neural radiance and explicit splatting representations side by side, and presents the results in an interactive client-side web viewer.

---

## 2. Objective
The objectives of this project are to:

* Build an end-to-end reconstruction pipeline that converts casual handheld monocular video into a navigable 3D scene representation of static indoor environments.
* Extract camera poses and sparse geometry from phone footage using Structure-from-Motion (COLMAP) [5], then train both a Neural Radiance Field baseline [1][3] and a 3D Gaussian Splatting model [2] on the recovered data.
* Evaluate the two approaches under matched conditions using PSNR, SSIM, LPIPS, training time, and rendering speed to identify practical trade-offs between volumetric and explicit representations.
* Deliver an interactive, browser-based viewer (Three.js / WebGL) that allows users to navigate the reconstructed scene at real-time frame rates without a backend GPU server.

---

## 3. Problem Description
Capturing 3D digital representations of real spaces remains difficult for non-specialist users. Traditional photogrammetry produces geometric meshes that often have visible seams, missing surfaces on featureless walls, and poor handling of reflective materials.

While neural view synthesis addresses many of these visual shortcomings, applying it to handheld smartphone video introduces practical complications:
1. Casual phone video suffers from motion blur, rolling shutter artifacts, and inconsistent exposure across frames.
2. Structure-from-Motion algorithms frequently struggle to resolve accurate camera trajectories when recording smooth indoor walls with minimal surface texture.
3. Neural volumetric techniques require substantial training time and computational resources, preventing real-time client-side exploration in standard web browsers.
4. Explicit primitive-based representations need careful pruning and parameter tuning to prevent visual artifacts ("floaters") in unobserved regions.

This project addresses these issues with a capture and reconstruction workflow built for monocular phone recordings. It evaluates rendering speed and visual quality across methods and exports the final representation to a lightweight web client.

---

## 4. Methodology
The proposed workflow consists of four modular stages:

```
[Phone Video] 
      │
      ▼
1. Pre-processing (Frame Extraction & Blur Filtering)
      │
      ▼
2. Camera Pose Estimation (COLMAP Structure-from-Motion)
      │
      ▼
3. Representation Training & Comparative Evaluation
   ├── Neural Radiance Baseline (Nerfacto / Instant-NGP)
   └── 3D Gaussian Splatting Pipeline
      │
      ▼
4. Export & Interactive Web Viewer (WebGL / Three.js)
```

The first stage is data acquisition and pre-processing. A user records a continuous, slow-orbit video of a static indoor scene using a smartphone at 1080p resolution and 30 frames per second. The recording is sampled into discrete frames, typically between 80 and 150. Each frame is scored with a Laplacian variance filter, and frames affected by motion blur are discarded so that only sharp images enter the reconstruction pipeline.

In the second stage, COLMAP [5] processes the filtered images through its Structure-from-Motion pipeline. It extracts SIFT feature descriptors, matches correspondences across viewpoints, and solves for camera intrinsics, extrinsics, and an initial sparse 3D point cloud. Ten to twenty percent of the recovered views are held out as test frames for later quantitative evaluation.

The third stage trains and evaluates two view synthesis approaches on the estimated camera poses. The first is a neural radiance baseline: a fast coordinate-based network, such as Instant-NGP [3] or Nerfacto via Nerfstudio [4], that optimizes color and volumetric density through sampled ray marching [1]. The second is 3D Gaussian Splatting [2], where millions of 3D ellipsoids are initialized from the sparse point cloud and their positions, rotations, scales, opacities, and spherical harmonic color coefficients are optimized using tiled differentiable rasterization. Both models train on the same split and are evaluated on the held-out views using Peak Signal-to-Noise Ratio (PSNR), Structural Similarity Index Measure (SSIM), Learned Perceptual Image Patch Similarity (LPIPS), training time, and peak GPU memory usage.

The fourth stage converts the trained scene representation into a web-compatible format such as `.ply` or compressed splat binaries. A front-end application built with Next.js, Three.js, and WebGL renders the scene directly in the browser. Users can orbit, pan, and zoom through the reconstructed space at real-time frame rates without sending rendering requests to a backend GPU server.

---

## 5. Project Scope

This project covers the full path from phone capture to interactive viewing of static indoor scenes. The input is casual monocular video recorded on a standard smartphone in controlled indoor settings such as desks, rooms, and corners. COLMAP [5] handles camera calibration and sparse point cloud generation. The core technical work is a comparative study: training a representative NeRF baseline [1][3][4] and a 3D Gaussian Splatting model [2] on the same captured datasets, then benchmarking them on visual fidelity (PSNR, SSIM, LPIPS), training duration, and rendering frame rate. The final deliverable is a client-side web application that lets users navigate the reconstructed 3D space in real time.

Several areas fall outside the scope of this project. The system does not handle dynamic scenes with moving people, non-rigid objects, or changing lighting during capture. It does not perform semantic parsing such as object segmentation, text querying, or instance identification. Scene editing capabilities like geometry modification, object removal, or generative inpainting are excluded. Model training remains an offline workstation task; there is no live camera tracking or on-device optimization. The project also does not include multi-user cloud deployment, database management, authentication, or multi-tenant server infrastructure.

---

## 6. Feasibility Study

The most likely point of failure in the pipeline is Structure-from-Motion. COLMAP [5] relies on matching visual features across frames, and low-texture surfaces like blank walls or rapid camera motion can prevent it from recovering accurate camera trajectories. To reduce this risk, the team will follow a structured capture protocol: slow orbital movement, consistent lighting, high frame overlap, and automated blur rejection before SfM runs. If a particular recording still fails to produce usable poses, standard public indoor benchmarks such as the Mip-NeRF 360 dataset [6] will substitute as evaluation data so that downstream work is not blocked.

GPU memory is a practical constraint. Dense indoor scenes with high frame counts can exceed available VRAM during optimization, particularly for 3D Gaussian Splatting where millions of primitives must be stored and updated simultaneously. To stay within a 16 GB VRAM budget, training images are downsampled by a factor of 2 to 4, and optimization parameters such as densification thresholds and maximum Gaussian counts are capped. These limits are consistent with the configurations reported in the original 3DGS paper [2].

Visual artifacts are another expected challenge. Regions of the scene with sparse camera coverage tend to develop cloudy "floaters" or oversized Gaussians that degrade rendering quality. Periodic opacity resets during training prune Gaussians that lack strong multi-view agreement, and bounding box cropping filters out distant background noise. Both techniques are standard practice in current 3DGS implementations [2].

On the viewer side, large scene files can cause slow load times and frame drops in the browser. Splat sorting optimizations, distance-based culling, and binary compression keep asset sizes small enough for responsive delivery over a standard network connection. The viewer targets WebGL, which is supported by all modern desktop and mobile browsers without plugins.

The hardware and software required for this project are accessible. The team has access to a workstation with an NVIDIA RTX A4000 GPU (16 GB VRAM), 32 GB of system memory, and an 8-core CPU. Scene capture requires only a standard smartphone recording at 1080p or higher. The software stack (Linux, CUDA 11.8/12.1, Python 3.10, PyTorch, COLMAP 3.8 [5], Nerfstudio [4], Node.js, and WebGL-compliant browsers) is entirely open-source or freely available, with no licensing costs.

---

## 7. Application Areas
* **Virtual Real Estate and Interior Tours:** Potential buyers and tenants can inspect realistic walkthroughs of residential and commercial properties generated from a simple phone recording.
* **Cultural Heritage and Museum Archiving:** Small institutions can document historical artifacts and exhibition rooms without investing in expensive laser scanning equipment.
* **E-Commerce Showrooms:** Merchants can present products in realistic 3D settings where customers can orbit and view items from any perspective online.
* **Site Survey and Insurance Documentation:** Inspectors can document physical spaces before and after renovations or incidents with accurate perspective reproduction.

---

## 8. Tools and Technology

| Category | Tool / Library | Role in Project |
| :--- | :--- | :--- |
| **Programming Languages** | Python 3.10, TypeScript | Offline reconstruction scripts, data loaders, and web front-end logic. |
| **Deep Learning Framework** | PyTorch, CUDA Toolkit | GPU tensor computation, gradient tracking, and custom rasterization kernels. |
| **Camera Pose Estimation** | COLMAP 3.8 | Structure-from-Motion, feature matching, and sparse point cloud generation. |
| **Neural View Synthesis** | Nerfstudio (Nerfacto / Instant-NGP) | Baseline volumetric neural radiance field training and evaluation. |
| **Gaussian Splatting** | 3D Gaussian Splatting (Diff-Gaussian-Rasterization) | Explicit scene parameterization and fast GPU rasterization. |
| **Evaluation Metrics** | TorchMetrics, scikit-image | Computation of PSNR, SSIM, and LPIPS against test views. |
| **Web Front-end & Rendering** | Next.js, Three.js | Interactive browser application for real-time orbit navigation and rendering. |

---

## 9. Expertise of the Team Members
Neither team member has taken a dedicated university course in Computer Graphics or Photogrammetry. Both members are studying 3D projective transformations, camera pinhole models, and rasterization techniques through technical documentation and open-source implementations.

The team has completed foundational coursework at Bahria University relevant to this project:
* **Computer Vision and Deep Learning (AIC 304, AIC 401):** Image filtering, feature extraction, camera projections, and neural network optimization.
* **Machine Learning and Artificial Intelligence (AIC 301, AIC 201):** Gradient-based training, loss functions, and model evaluation protocols.
* **Mathematics for AI (GSC 121, GSC 211):** Linear algebra, rotation representations (quaternions and matrices), affine coordinates, and multivariable calculus.
* **High-Performance Computing (AIC 302):** Parallel computing principles, memory hierarchy, and GPU execution models.
* **Software Engineering and Web Development (SEN 220, CSC 221):** Modular architecture, data structures for spatial indexing, and client-side web application development.

---

## 10. Milestones

| Period / Month | Milestone Focus | Deliverables and Criteria | Academic Checkpoint |
| :--- | :--- | :--- | :--- |
| **Month 1 (Sep 2026)** | Literature Review and Setup | Review NeRF and 3DGS publications. Establish development environment with CUDA, COLMAP, and PyTorch. | Proposal Presentation (Week 3) |
| **Month 2 (Oct 2026)** | Data Capture and SfM Pipeline | Establish phone capture protocol. Collect initial indoor scenes. Run COLMAP to extract reliable poses and sparse point clouds. | Initial Project Defense (Week 8) |
| **Months 3-4 (Nov-Dec 2026)** | Baseline Model Training | Train neural radiance baseline (Nerfstudio/Instant-NGP) and initial 3DGS models on captured scenes. Profile training time and memory usage. | Midterm Project Defense (Week 16) |
| **Months 5-6 (Jan-Feb 2027)** | Comparative Evaluation & Optimization | Perform side-by-side evaluation (PSNR, SSIM, LPIPS, FPS). Tune densification parameters to minimize visual artifacts. | 8th Semester Core Work |
| **Month 7 (Mar 2027)** | Web Viewer Integration | Export optimized scene assets. Implement client-side Three.js/WebGL viewer with smooth orbit controls and real-time rendering. | Pre-submission Review |
| **Month 8 (Apr-May 2027)** | Final Documentation and Defense | Complete technical report, prepare demonstration backups, showcase system at university Open House, and defend project. | Final Defense (Week 15) |

---

## 11. References
1. Mildenhall, B., Srinivasan, P.P., Tancik, M., Barron, J.T., Ramamoorthi, R. and Ng, R., 2021. 'NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis', *Communications of the ACM*, 65(1), pp. 99-106.
2. Kerbl, B., Kopanas, G., Leimkuehler, T. and Drettakis, G., 2023. '3D Gaussian Splatting for Real-Time Radiance Field Rendering', *ACM Transactions on Graphics*, 42(4), pp. 139:1-139:14.
3. Müller, T., Evans, A., Schied, C. and Keller, A., 2022. 'Instant Neural Graphics Primitives with a Multiresolution Hash Encoding', *ACM Transactions on Graphics*, 41(4), pp. 102:1-102:15.
4. Tancik, M., Weber, E., Ng, E., Li, R., Iyer, B., Kerr, J., Matthew, T., Nempe, A., Saraswat, P. and Kanazawa, A., 2023. 'Nerfstudio: A Modular Framework for Neural Radiance Field Development', *ACM SIGGRAPH 2023 Conference Proceedings*, pp. 1-12.
5. Schönberger, J.L. and Frahm, J.M., 2016. 'Structure-from-Motion Revisited', *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, pp. 4104-4113.
6. Barron, J.T., Mildenhall, B., Verbin, D., Srinivasan, P.P. and Hedman, P., 2022. 'Mip-NeRF 360: Unbounded Anti-Aliased Neural Radiance Fields', *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, pp. 5470-5479.

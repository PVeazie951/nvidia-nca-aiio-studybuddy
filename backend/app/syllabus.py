"""NCA-AIIO syllabus seed data.

Topics follow the published exam blueprint for the NVIDIA-Certified Associate,
AI Infrastructure and Operations (NCA-AIIO). Weights are the approximate share
of exam content and are editable in the UI.
"""

SEED_TOPICS: list[dict] = [
    {
        "slug": "ai-fundamentals",
        "title": "AI, ML & Deep Learning Fundamentals",
        "description": "AI vs ML vs DL, training vs inference, model lifecycle, common workloads.",
        "weight": 10,
    },
    {
        "slug": "gpu-architecture",
        "title": "GPU & Accelerator Architecture",
        "description": "GPU vs CPU design, SMs, CUDA cores, tensor cores, VRAM, HBM vs GDDR.",
        "weight": 14,
    },
    {
        "slug": "nvidia-gpu-platforms",
        "title": "NVIDIA GPU Platforms & Specs",
        "description": "Data-center vs workstation vs consumer lines, generation names, key specs.",
        "weight": 12,
    },
    {
        "slug": "system-architecture",
        "title": "Server & System Architecture",
        "description": "PCIe generations, NVLink/NVSwitch, HGX/DGX, GPUDirect, topology.",
        "weight": 13,
    },
    {
        "slug": "networking",
        "title": "AI Networking & Interconnects",
        "description": "InfiniBand vs Ethernet, RoCE, RDMA, DPUs, scale-up vs scale-out.",
        "weight": 11,
    },
    {
        "slug": "storage",
        "title": "Storage for AI Workloads",
        "description": "Tiers, filesystems, throughput needs, checkpointing, caching layers.",
        "weight": 8,
    },
    {
        "slug": "software-stack",
        "title": "AI Software Stack & Frameworks",
        "description": "CUDA, cuDNN, TensorRT, drivers, containers, NGC, framework layers.",
        "weight": 12,
    },
    {
        "slug": "orchestration",
        "title": "Orchestration & Cluster Management",
        "description": "Kubernetes, GPU Operator, schedulers, MIG, multi-tenancy.",
        "weight": 8,
    },
    {
        "slug": "deployment-models",
        "title": "Deployment Models & Cloud",
        "description": "On-prem, cloud, hybrid, multi-cloud, colocation, TCO tradeoffs.",
        "weight": 6,
    },
    {
        "slug": "operations",
        "title": "Monitoring, Troubleshooting & Operations",
        "description": "Telemetry, DCGM, health checks, thermal/power limits, failure modes.",
        "weight": 6,
    },
]

# ZCAD Repository Architecture

ZCAD is divided into a reusable engine and a product repository.

## `zcad-core`

Python namespace: `zcad_core`

The core owns product-independent CAD infrastructure:

- reusable modeling features
- assembly data models and validation
- manufacturing-profile loading
- profile-aware validation
- build metadata
- STEP and STL export services

The core follows semantic versioning. `cad-automation` currently supports
`zcad-core` versions `>=0.1,<0.2`.

## `cad-automation`

Python namespace: `zcad`

The product owns:

- command-line orchestration
- design-file interpretation
- parametric product generators
- enclosure, tray, coupon, and Gridfinity-inspired designs
- product-specific tests and examples

Product generators may use `zcad_core`, but the core must never import `zcad`.

## Local development

The repositories are expected to be sibling directories:

```text
dev/
├── cad-automation/
└── zcad-core/
```

Bootstrap the product environment with:

```bash
./scripts/bootstrap-dev.sh
```

A different core checkout may be selected with:

```bash
ZCAD_CORE_ROOT=/path/to/zcad-core ./scripts/bootstrap-dev.sh
```

Until `zcad-core` is published or assigned a Git remote, a fresh environment must install the local core checkout before installing `cad-automation`.

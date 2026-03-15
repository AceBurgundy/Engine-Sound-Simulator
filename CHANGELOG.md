# Engine Class Changes

This document describes the differences between the **original `Engine` class** from the *Engine Sound Simulator* and the **refactored `Engine` class** introduced in *Engine Sound Simulator+++*.

The new implementation significantly expands the capabilities of the engine simulation while improving code clarity, extensibility, and synthesis realism.

# 1. Architectural Changes

## Original Engine Class

The original engine class implemented a **single synthesis model**: procedural engine cycle synthesis.

This approach generates audio by:

1. Computing timing between cylinder firing events.
2. Slicing pre-generated audio buffers.
3. Concatenating and overlaying buffers for each cylinder.
4. Looping the resulting engine cycle.

### Original Architecture

```

engine.gen_audio()
→ _gen_audio_one_engine_cycle()
→ audio_tools.slice()
→ audio_tools.concat()
→ audio_tools.overlay()

```

## New Engine Class

The new engine supports **two synthesis modes**:

1. **Procedural engine cycle synthesis** *(original method)*
2. **Granular combustion playback** *(new)*

```

generate_audio()
├── _generate_audio_one_engine_cycle()
└── _generate_audio_pop_mode()

````

This introduces a **dual synthesis architecture**, enabling significantly more realistic combustion modeling.

# 2. New Features

## Granular Combustion Playback ("pop mode")

The most significant addition is **granular synthesis**, which produces engine sound by spawning many short combustion samples called **grains**.

### New Parameters

- `pop_sample`
- `pop_mode`
- `active_grains`
- `time_since_last_fire`

### New Functions

- `_spawn_grain()`
- `_generate_audio_pop_mode()`

## Grain Spawning

Each grain represents a **single combustion event**.

A grain is created with small randomized variations to simulate real-world combustion behavior.

### Randomized Properties

$$
pitch = 1 \pm \text{small random variation}
$$

$$
volume = 1 \pm \text{small random variation}
$$

### Pitch Shifting Implementation

Pitch shifting is implemented using interpolation:

```python
indices = arange(0, len(pop_sample), pitch)
grain = interp(indices, arange(len(pop_sample)), pop_sample)
````

# 3. Exhaust Resonance Simulation

A new feature called `exhaust_resonance` simulates pipe resonance using a high-pass filter.

### Implementation

```python
output = convolve(output, [1, -0.97])
```

### DSP Interpretation

In digital signal processing terms this behaves as a **differentiator filter**:

$$
y[n] = x[n] - 0.97 \cdot x[n-1]
$$

This emphasizes higher frequencies and increases the perceived sharpness of exhaust pulses.

# 4. Unequal Cylinder Timing Support

A new parameter enables simulation of **uneven firing delays**:

```
unequal: List[int]
```

This allows modeling of:

* Cross-plane crank engines
* Big-bang firing orders
* Experimental or irregular firing patterns

### Delay Calculation

$$
delay_{seconds} = \frac{unequal[cylinder]}{1000}
$$

Buffers are separated into:

* `equal_buffers`
* `unequal_buffers`

These are recombined later to preserve proper timing alignment.

# 5. Engine Timing Improvements

Timing conversion was rewritten using a **cumulative timing model** that converts relative timing into absolute offsets.

### Timing Conversion

$$
timing[0] = 0
$$

$$
timing[i] = timing[i] + timing[i-1]
$$

This approach simplifies the calculation of firing offsets during synthesis.

# 6. Method and Configuration Refactor

## Method Renaming

| Old Name                        | New Name                             |
| ------------------------------- | ------------------------------------ |
| `gen_audio()`                   | `generate_audio()`                   |
| `_gen_audio_one_engine_cycle()` | `_generate_audio_one_engine_cycle()` |

## Modular Imports

Configuration loading was moved from a flat import:

```
import cfg
```

to a modular package structure:

```python
import core.configurations as configurations
```

## NumPy Import Optimization

Specific functions are now imported directly for improved static analysis and startup performance.

```python
from numpy import array, zeros, arange, interp, convolve
```

# 7. RPM Control and Synchronization

## Updated RPM Logic

Throttle behavior was adjusted to provide smoother transitions.

### Original Behavior

$$
rpm \leftarrow rpm + \frac{1000}{strokes}
$$

$$
rpm \leftarrow rpm - \min(125, rpm - idle)
$$

### New Behavior

$$
rpm \leftarrow rpm + \frac{100}{4}
$$

$$
rpm \leftarrow rpm - \min(50, rpm - idle)
$$

## External RPM Synchronization

A new method `adjust_rpm()` synchronizes the engine simulation with external inputs such as motorcycle telemetry.

### Scaling Formula

$$
scale = \frac{RPM_{current} - RPM_{idle}}{RPM_{limit} - RPM_{idle}}
$$

### Adjusted RPM

$$
RPM_{adj} = Engine_{idle} + \left(scale \cdot (Engine_{limit} - Engine_{idle})\right)
$$

# 8. Summary Comparison

| Feature                     | Original Engine | New Engine |
| --------------------------- | --------------- | ---------- |
| **Procedural Synthesis**    | ✓               | ✓          |
| **Granular Synthesis**      | ✗               | ✓          |
| **Exhaust Resonance**       | ✗               | ✓          |
| **Unequal Cylinder Delays** | ✗               | ✓          |
| **External RPM Control**    | ✗               | ✓          |
| **Type Hints**              | ✗               | ✓          |
| **Modular Configuration**   | ✗               | ✓          |
| **Documentation**           | Minimal         | Extensive  |

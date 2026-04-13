# Multimodal Input - Complete Guide
### imp! 
## What is Multimodal?

**Multimodal** = Supporting multiple input types (modalities)

**Modalities:**
- 📝 **Text** - Typed messages
- 🎤 **Voice** - Speech audio
- 🖼️ **Image** - Photos, screenshots, diagrams
- 🎥 **Video** - Motion pictures (future)
- 📄 **Documents** - PDFs, Word files (future)

## Why Multimodal Matters

### Real-World Scenarios

**Scenario 1: Travel Planning**
```
Text:  "Plan a trip to Tokyo"
Voice: [User speaks while driving]
Image: Photo of hotel brochure
```

**Scenario 2: Home Renovation**
```
Text:  "Redesign my kitchen"
Image: Current kitchen photo
Image: Inspiration Pinterest screenshot
Voice: "I want more counter space"
```

**Scenario 3: Project Management**
```
Text:  "Review this project plan"
Image: Gantt chart screenshot
Voice: "What about the budget?"
```

### Benefits

✅ **Natural interaction** - Use best modality for context
✅ **Accessibility** - Voice for hands-free, text for deaf users
✅ **Richer context** - Image shows what words can't describe
✅ **Faster input** - Voice is faster than typing

---

## Modality Normalization Concept

### The Problem

Each modality has different data types:

```python
text_input = "Plan my week"              # String
voice_input = audio_bytes                 # Binary audio data
image_input = image_pixels                # Binary image data
```

**LLMs can only process text!**

### The Solution: Normalization

Convert everything to text before reasoning:

```python
text_input   → "Plan my week"              # Direct
voice_input  → "Plan my week"              # Speech-to-text
image_input  → "Calendar with deadlines"   # Image captioning
```

### Normalization Pipeline

```
┌─────────────────────────────────────────────────────┐
│ RAW INPUT (Different Types)                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Text:   "Plan trip"                               │
│  Voice:  [Audio bytes: 0x48656c6c6f...]            │
│  Image:  [Image pixels: RGB(255,255,255)...]       │
│                                                     │
└─────────────────────────────────────────────────────┘
                      ↓
        ┌─────────────────────────────┐
        │  MODALITY PROCESSORS        │
        └─────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ NORMALIZED TEXT                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Text:   "Plan trip"                               │
│  Voice:  "[Transcribed] Plan trip"                 │
│  Image:  "[Image] Vacation destination brochure"   │
│                                                     │
└─────────────────────────────────────────────────────┘
                      ↓
        ┌─────────────────────────────┐
        │  REASONING ENGINE           │
        │  (Only sees text!)          │
        └─────────────────────────────┘
```

---

## Modality Processing Details

### 1. Text Processing

**Input:** String
**Processing:** None (already text)
**Output:** Same string

```python
def text_processor(state):
    return {"extracted_text": state["raw_input_payload"]}
```

**Example:**
```
Input:  "Plan a 3-day Tokyo trip"
Output: "Plan a 3-day Tokyo trip"
```

**Latency:** <1ms
**Cost:** Free
**Accuracy:** 100%

---

### 2. Voice Processing (Speech-to-Text)

**Input:** Audio file (.mp3, .wav, .m4a)
**Processing:** Speech recognition (Whisper)
**Output:** Transcribed text

#### Current Implementation (Mock)

```python
def voice_processor_mock(state):
    # Mock: Just wrap the input
    return {
        "extracted_text": f"[Transcribed]: {state['raw_input_payload']}",
        "metadata": {
            "confidence": 0.95,
            "language": "en"
        }
    }
```

#### Future Implementation (Whisper API)

```python
async def voice_processor_real(state):
    import openai

    audio_file = open(state["raw_input_payload"], "rb")

    transcript = await openai.Audio.atranscribe(
        model="whisper-1",
        file=audio_file,
        language="en"  # Optional: Auto-detect if omitted
    )

    return {
        "extracted_text": transcript.text,
        "metadata": {
            "processor": "whisper",
            "confidence": 0.95,  # Whisper doesn't provide this
            "language": transcript.language,
            "duration": transcript.duration
        }
    }
```

**Example:**
```
Input:  audio.mp3 (User saying "Plan my week")
Output: "Plan my week"
```

**Latency:** 1-3 seconds
**Cost:** $0.006/minute
**Accuracy:** ~95%

#### Handling Edge Cases

**Background Noise:**
```python
if transcript.confidence < 0.7:
    return {
        "extracted_text": "[Low quality audio] " + transcript.text,
        "metadata": {"needs_confirmation": True}
    }
```

**Multiple Languages:**
```python
transcript = await openai.Audio.atranscribe(
    model="whisper-1",
    file=audio_file,
    language=None  # Auto-detect
)
```

**Long Audio:**
```python
# Split into chunks if > 25MB
if file_size > 25_000_000:
    chunks = split_audio(audio_file, chunk_duration=30)
    transcripts = [await transcribe(chunk) for chunk in chunks]
    full_transcript = " ".join(transcripts)
```

---

### 3. Image Processing (Vision-to-Text)

**Input:** Image file (.jpg, .png, .webp)
**Processing:** Image captioning / Visual understanding
**Output:** Text description

#### Current Implementation (Mock)

```python
def image_processor_mock(state):
    # Mock: Just wrap the input
    return {
        "extracted_text": f"[Image description]: {state['raw_input_payload']}",
        "metadata": {
            "detected_objects": ["placeholder"],
            "scene": "unknown"
        }
    }
```

#### Future Implementation (GPT-4 Vision)

```python
async def image_processor_real(state):
    import openai
    import base64

    # Encode image to base64
    with open(state["raw_input_payload"], "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    response = await openai.ChatCompletion.acreate(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image in detail for planning context. Include objects, text, layout, and relevant details."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "high"  # or "low" for faster processing
                    }
                }
            ]
        }],
        max_tokens=300
    )

    description = response.choices[0].message.content

    return {
        "extracted_text": description,
        "metadata": {
            "processor": "gpt-4-vision",
            "model": response.model,
            "tokens_used": response.usage.total_tokens
        }
    }
```

**Example:**
```
Input:  kitchen_photo.jpg
Output: "A modern kitchen with white cabinets, stainless steel appliances,
         marble countertops, and a large island. Natural light from window.
         Approximately 200 sq ft."
```

**Latency:** 2-5 seconds
**Cost:** $0.01 - $0.03 per image
**Accuracy:** ~90% for general descriptions

#### Advanced Image Processing

**OCR (Text Extraction):**
```python
from PIL import Image
import pytesseract

def extract_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text

# Combined with vision:
def image_processor_with_ocr(state):
    # Get visual description
    visual_desc = await gpt4_vision.describe(state["raw_input_payload"])

    # Extract any text
    extracted_text = extract_text_from_image(state["raw_input_payload"])

    combined = f"{visual_desc}\n\nText in image: {extracted_text}"

    return {"extracted_text": combined}
```

**Object Detection:**
```python
from transformers import pipeline

detector = pipeline("object-detection", model="facebook/detr-resnet-50")

def detect_objects(image_path):
    results = detector(image_path)
    objects = [r['label'] for r in results]
    return objects

# Example:
# Input: office_photo.jpg
# Output: ["desk", "chair", "laptop", "monitor", "plant"]
```

**Scene Classification:**
```python
from transformers import pipeline

classifier = pipeline("image-classification", model="microsoft/resnet-50")

def classify_scene(image_path):
    results = classifier(image_path)
    scene = results[0]['label']
    return scene

# Example:
# Input: photo.jpg
# Output: "indoor", "kitchen", "modern"
```

---

## Metadata Enrichment

Each processor adds metadata for context:

### Text Metadata
```python
{
    "processor": "text",
    "processed_at": "2024-01-15T10:30:00",
    "word_count": 5
}
```

### Voice Metadata
```python
{
    "processor": "voice",
    "confidence": 0.95,
    "language": "en",
    "duration": 3.5,  # seconds
    "speaker_count": 1,
    "background_noise": "low",
    "processed_at": "2024-01-15T10:30:00"
}
```

### Image Metadata
```python
{
    "processor": "image",
    "image_path": "/uploads/kitchen.jpg",
    "detected_objects": ["countertop", "cabinet", "appliance"],
    "scene_type": "kitchen",
    "has_text": True,
    "extracted_text": "Recipe Book",
    "dimensions": {"width": 1920, "height": 1080},
    "file_size": 2.5,  # MB
    "processed_at": "2024-01-15T10:30:00"
}
```

---

## Error Handling

### Voice Processing Errors

```python
try:
    transcript = await whisper.transcribe(audio_file)
except AudioQualityError:
    return {
        "extracted_text": "[Unable to transcribe - poor audio quality]",
        "metadata": {"error": "low_quality", "needs_retry": True}
    }
except UnsupportedLanguageError:
    return {
        "extracted_text": "[Language not supported]",
        "metadata": {"error": "unsupported_language"}
    }
except FileTooLargeError:
    return {
        "extracted_text": "[Audio file too large - please split]",
        "metadata": {"error": "file_too_large", "max_size_mb": 25}
    }
```

### Image Processing Errors

```python
try:
    description = await gpt4_vision.describe(image_file)
except InvalidImageError:
    return {
        "extracted_text": "[Invalid image format]",
        "metadata": {"error": "invalid_format", "supported": [".jpg", ".png"]}
    }
except ImageTooLargeError:
    return {
        "extracted_text": "[Image too large - please resize]",
        "metadata": {"error": "too_large", "max_size_mb": 20}
    }
except InappropriateContentError:
    return {
        "extracted_text": "[Image contains inappropriate content]",
        "metadata": {"error": "inappropriate_content"}
    }
```

---

## Cost Optimization

### Voice Processing

**Whisper API Pricing:** $0.006/minute

**Optimization strategies:**
```python
# 1. Detect silence and trim
audio = trim_silence(audio_file, threshold_db=-40)

# 2. Compress audio (lower quality for speech)
audio = compress_audio(audio, bitrate="32k")

# 3. Use VAD (Voice Activity Detection)
speech_segments = detect_speech(audio)
transcribe_only(speech_segments)  # Skip silence

# Cost reduction: ~30-50%
```

### Image Processing

**GPT-4 Vision Pricing:** $0.01-$0.03 per image

**Optimization strategies:**
```python
# 1. Use "low" detail for simple images
response = await gpt4_vision.describe(
    image,
    detail="low"  # Cheaper, faster
)

# 2. Resize large images
if image_size > 2MB:
    image = resize_image(image, max_dimension=1024)

# 3. Cache descriptions for duplicate images
cache_key = hash_image(image)
if cache_key in cache:
    return cache[cache_key]

# Cost reduction: ~40-60%
```

---

## Best Practices

### 1. Always Validate Input
```python
def validate_input(input_type, payload):
    if input_type == "voice":
        if not payload.endswith((".mp3", ".wav", ".m4a")):
            raise ValueError("Invalid audio format")
        if file_size(payload) > 25_000_000:
            raise ValueError("Audio file too large")

    elif input_type == "image":
        if not payload.endswith((".jpg", ".png", ".webp")):
            raise ValueError("Invalid image format")
        if file_size(payload) > 20_000_000:
            raise ValueError("Image file too large")
```

### 2. Provide Fallbacks
```python
try:
    extracted_text = await process_modality(state)
except ProcessingError:
    # Fallback to text input
    extracted_text = "[Processing failed - please describe in text]"
    state["input_type"] = "text"
```

### 3. Use Appropriate Detail Levels
```python
# For thumbnails/previews: low detail
if image_purpose == "preview":
    detail = "low"

# For detailed analysis: high detail
elif image_purpose == "detailed_planning":
    detail = "high"
```

### 4. Handle Timeouts
```python
try:
    result = await asyncio.wait_for(
        process_image(image),
        timeout=10.0  # 10 second timeout
    )
except asyncio.TimeoutError:
    return {"extracted_text": "[Processing timeout - please retry]"}
```

---

## Future Modalities

### Video Processing
```python
async def video_processor(state):
    # Extract keyframes
    frames = extract_keyframes(state["raw_input_payload"])

    # Process each frame
    descriptions = [await describe_frame(f) for f in frames]

    # Combine into narrative
    narrative = combine_temporal_context(descriptions)

    return {"extracted_text": narrative}
```

### PDF Processing
```python
async def pdf_processor(state):
    # Extract text
    text = extract_pdf_text(state["raw_input_payload"])

    # Extract images
    images = extract_pdf_images(state["raw_input_payload"])

    # Process images
    image_descriptions = [await describe(img) for img in images]

    # Combine
    combined = f"Document text: {text}\n\nImages: {image_descriptions}"

    return {"extracted_text": combined}
```

---

## Summary

### Key Concepts

1. **Multimodal** = Multiple input types
2. **Normalization** = Convert all to text
3. **Modality Agnostic** = Reasoning layer doesn't care about input type
4. **Metadata** = Enrich context with processing details
5. **Error Handling** = Graceful degradation

### Why This Matters

**Without multimodal:**
- User must type everything
- Can't leverage voice or images
- Limited accessibility

**With multimodal:**
- Natural interaction (use best modality)
- Richer context (images show more)
- Better accessibility (voice for hands-free)

### Implementation Pattern

```python
# 1. Detect modality
input_type = detect_type(input)

# 2. Process with appropriate processor
if input_type == "text":
    extracted = process_text(input)
elif input_type == "voice":
    extracted = process_voice(input)
elif input_type == "image":
    extracted = process_image(input)

# 3. Reason with normalized text
plan = generate_plan(extracted)

# 4. Respond
return stream_response(plan)
```

**Bottom Line:** Multimodal systems provide natural, accessible, context-rich interactions by normalizing diverse inputs into text for unified reasoning.

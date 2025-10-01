# FaceScannerPro - Technical Overview
# FaceScannerPro - နည်းပညာဆိုင်ရာ အကြမ်းဖျင်းဖော်ပြချက်

## English Version

### Project Overview
FaceScannerPro is an advanced real-time face recognition and tracking system that combines state-of-the-art deep learning models with efficient tracking algorithms. The system provides robust person identification in video streams through a modern graphical user interface.

### Core Technologies and Libraries

#### 1. Face Recognition Framework
- **InsightFace (buffalo_l model)**
  - **Purpose**: Primary face recognition engine
  - **Technology**: Deep neural network-based face recognition
  - **Model**: buffalo_l - 512-dimensional face embeddings
  - **Theory**: ArcFace loss function for improved face feature learning
  - **Performance**: State-of-the-art accuracy on standard benchmarks
  - **Implementation**: ONNX Runtime for optimized inference

#### 2. Object Tracking System
- **DeepSORT (Deep Simple Online and Realtime Tracking)**
  - **Purpose**: Multi-object tracking with temporal consistency
  - **Components**:
    - Kalman Filter: Motion prediction and state estimation
    - Hungarian Algorithm: Optimal assignment between detections and tracks
    - Deep Association Metric: Appearance-based re-identification
  - **Theory**: Combines motion and appearance cues for robust tracking
  - **Library**: `deep-sort-realtime`

#### 3. Computer Vision Foundation
- **OpenCV (cv2)**
  - **Purpose**: Image processing and video capture
  - **Functions**: 
    - Video I/O operations
    - Image preprocessing and manipulation
    - Drawing annotations and overlays
  - **Backend**: DirectShow (Windows) for camera compatibility

#### 4. Mathematical Computing
- **NumPy**
  - **Purpose**: Numerical computations and array operations
  - **Usage**: 
    - Embedding vector operations
    - Cosine distance calculations
    - Matrix manipulations for face alignment

#### 5. Database Management
- **SQLite3**
  - **Purpose**: Lightweight database for storing person data and embeddings
  - **Schema**: 
    - People table: Personal information storage
    - Embeddings table: Face feature vectors
    - Events table: Tracking history and logs
  - **Optimization**: Indexed queries for real-time performance

#### 6. User Interface Framework
- **Tkinter with TTK**
  - **Purpose**: Modern desktop GUI application
  - **Features**:
    - Tabbed interface design
    - Real-time video display
    - Responsive layout management
    - Custom styling and themes

#### 7. Image Processing and Display
- **PIL (Python Imaging Library)**
  - **Purpose**: Image format conversion and display
  - **Usage**: Converting OpenCV images to Tkinter-compatible format

#### 8. Machine Learning Runtime
- **ONNX Runtime**
  - **Purpose**: Optimized inference engine for deep learning models
  - **Benefits**: Cross-platform compatibility and performance optimization
  - **Providers**: CPU and GPU execution providers

### Technical Methodologies

#### 1. Face Recognition Pipeline

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Input Frame   │───▶│  Face Detection │───▶│ Face Alignment  │
│                 │    │                 │    │                 │
│ • Video Stream  │    │ • SCRFD Model   │    │ • 5-point       │
│ • Image Buffer  │    │ • Confidence    │    │   Landmarks     │
│ • Resolution:   │    │   Threshold     │    │ • Geometric     │
│   640x480       │    │ • Bounding Box  │    │   Normalization │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲                       │
                                │                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Quality Check  │    │Feature Extraction│
                       │                 │    │                 │
                       │ • Face Size     │    │ • Buffalo_l CNN │
                       │ • Blur Level    │    │ • 512-dim       │
                       │ • Pose Angle    │    │   Embedding     │
                       │ • Lighting      │    │ • Normalization │
                       └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│Identity Assignment│◀───│Similarity Matching│◀───│Gallery Database │
│                 │    │                 │    │                 │
│ • Person Name   │    │ • Cosine        │    │ • Known Person  │
│ • Confidence    │    │   Distance      │    │   Embeddings    │
│ • Track ID      │    │ • Threshold:    │    │ • Metadata      │
│ • Timestamp     │    │   0.4 (Match)   │    │ • SQLite Store  │
└─────────────────┘    │   0.65 (Unknown)│    └─────────────────┘
                       └─────────────────┘
```

**Detailed Process Flow:**

1. **Input Processing**
   ```
   Video Frame (BGR) → Preprocessing → RGB Conversion → Resize if needed
   ```

2. **Face Detection (SCRFD)**
   ```
   RGB Image → Neural Network → Bounding Boxes → Confidence Scores → Filter by Threshold
   ```

3. **Quality Assessment**
   ```
   Face Crop → Size Check → Blur Detection → Pose Estimation → Accept/Reject
   ```

4. **Face Alignment**
   ```
   Face Crop → Landmark Detection → Affine Transformation → Normalized Face (112x112)
   ```

5. **Feature Extraction**
   ```
   Normalized Face → Buffalo_l CNN → Raw Features → L2 Normalization → 512-dim Vector
   ```

6. **Similarity Matching**
   ```
   Query Embedding → Gallery Comparison → Cosine Distance → Best Match → Threshold Check
   ```

**Process Details:**
- **Detection**: SCRFD (Sample and Computation Redistributed Face Detector)
- **Alignment**: Landmark-based geometric normalization
- **Extraction**: Deep CNN for 512-dimensional embeddings
- **Matching**: Cosine similarity with adaptive thresholding

#### 2. Tracking Algorithm (DeepSORT)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Previous Tracks │───▶│Motion Prediction│───▶│  New Detections │
│                 │    │                 │    │                 │
│ • Track State   │    │ • Kalman Filter │    │ • Face Boxes    │
│ • Position      │    │ • Velocity      │    │ • Appearance    │
│ • Velocity      │    │ • Uncertainty   │    │ • Confidence    │
│ • Appearance    │    │ • Prediction    │    │ • Features      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │  Cost Matrix    │◀───│  Association    │
         │              │                 │    │                 │
         │              │ • Motion Cost   │    │ • Hungarian     │
         │              │ • Appearance    │    │   Algorithm     │
         │              │   Cost          │    │ • Optimal       │
         │              │ • Combined      │    │   Assignment    │
         │              │   Distance      │    │ • Unmatched     │
         │              └─────────────────┘    └─────────────────┘
         │                                              │
         │                                              ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │  Track Update   │◀───│ Track Management│
         │              │                 │    │                 │
         │              │ • Position      │    │ • Confirmed     │
         │              │ • Velocity      │    │ • Tentative     │
         │              │ • Appearance    │    │ • Deleted       │
         │              │ • Age Counter   │    │ • New Tracks    │
         │              └─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
```

**DeepSORT State Machine:**
```
New Detection → Tentative Track → Confirmed Track → Deleted Track
     │              │ (n_init=3)        │ (max_age=7)      │
     │              │                   │                   │
     └──────────────▼───────────────────▼───────────────────┘
                 Track Lifecycle Management
```

**Key Components:**

1. **Kalman Filter (Motion Model)**
   ```
   State Vector: [x, y, aspect_ratio, height, vx, vy, va, vh]
   Prediction:   x̂(k|k-1) = F·x̂(k-1|k-1) + B·u(k)
   Update:       x̂(k|k) = x̂(k|k-1) + K(k)·[z(k) - H·x̂(k|k-1)]
   ```

2. **Appearance Descriptor**
   ```
   Face Crop → ResNet Features → L2 Normalization → 128-dim Vector
   ```

3. **Cost Calculation**
   ```
   Total Cost = λ₁ × Motion Cost + λ₂ × Appearance Cost
   Motion Cost = Mahalanobis Distance
   Appearance Cost = Cosine Distance
   ```

**DeepSORT Components:**
- **Kalman Filter**: Predicts object motion using linear dynamics
- **Hungarian Algorithm**: Solves assignment problem for optimal track-detection pairing
- **Appearance Descriptor**: Deep features for re-identification across occlusions

#### 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FaceScannerPro System Architecture                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │  Presentation   │◀──▶│   Business      │◀──▶│      Data       │          │
│  │     Layer       │    │    Logic        │    │     Layer       │          │
│  │                 │    │    Layer        │    │                 │          │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │          │
│  │ │Modern GUI   │ │    │ │Video Worker │ │    │ │SQLite DB    │ │          │
│  │ │• Tkinter    │ │    │ │• Threading  │ │    │ │• People     │ │          │
│  │ │• TTK Style  │ │    │ │• Pipeline   │ │    │ │• Embeddings │ │          │
│  │ │• Tabs       │ │    │ │• Real-time  │ │    │ │• Events     │ │          │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │          │
│  │                 │    │                 │    │                 │          │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │          │
│  │ │Live Video   │ │    │ │Face Engine  │ │    │ │File Storage │ │          │
│  │ │• Display    │ │    │ │• InsightFace│ │    │ │• Images     │ │          │
│  │ │• Controls   │ │    │ │• ONNX RT    │ │    │ │• Models     │ │          │
│  │ │• Stats      │ │    │ │• Recognition│ │    │ │• Logs       │ │          │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │          │
│  │                 │    │                 │    │                 │          │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │                 │          │
│  │ │Detection    │ │    │ │Tracking     │ │    │                 │          │
│  │ │Panel        │ │    │ │• DeepSORT   │ │    │                 │          │
│  │ │• Cards      │ │    │ │• Kalman     │ │    │                 │          │
│  │ │• Info       │ │    │ │• Hungarian  │ │    │                 │          │
│  │ └─────────────┘ │    │ └─────────────┘ │    │                 │          │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   External      │
                              │   Components    │
                              │                 │
                              │ ┌─────────────┐ │
                              │ │Camera/Video │ │
                              │ │• USB Camera │ │
                              │ │• IP Camera  │ │
                              │ │• Video File │ │
                              │ └─────────────┘ │
                              │                 │
                              │ ┌─────────────┐ │
                              │ │ML Models    │ │
                              │ │• buffalo_l  │ │
                              │ │• SCRFD      │ │
                              │ │• RetinaFace │ │
                              │ └─────────────┘ │
                              └─────────────────┘
```

**Data Flow Architecture:**
```
Camera → OpenCV → Face Detection → Feature Extraction → Database → UI Display
   │         │          │               │                  │          │
   │         │          │               │                  │          └─► User Interaction
   │         │          │               │                  └─► Track History
   │         │          │               └─► Similarity Matching
   │         │          └─► DeepSORT Tracking
   │         └─► Frame Processing
   └─► Video Stream
```

#### 4. Database Schema

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Database Schema Design                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐       ┌─────────────────────┐       ┌─────────────────────┐
│      PEOPLE         │       │    EMBEDDINGS       │       │       EVENTS        │
├─────────────────────┤       ├─────────────────────┤       ├─────────────────────┤
│ id (PK)            │◀──────│ id (PK)            │       │ id (PK)            │
│ name (UNIQUE)      │       │ person_id (FK)     │       │ timestamp          │
│ phone              │       │ vec (BLOB)         │       │ track_id           │
│ dob                │       │ norm (REAL)        │       │ person_id (FK)     │
│ link               │       │ src_path           │       │ name               │
│ info               │       │ created_at         │       │ confidence         │
│ social_link        │       └─────────────────────┘       │ frame_path         │
│ info1              │                                     │ kind               │
│ note               │                                     └─────────────────────┘
│ created_at         │                │                            │
└─────────────────────┘                │                            │
         │                             │                            │
         └─────────────────────────────┘                            │
                                                                    │
┌─────────────────────┐                                            │
│     SETTINGS        │                                            │
├─────────────────────┤                                            │
│ key (PK)           │                                            │
│ value              │                                            │
└─────────────────────┘                                            │
                                                                    │
                                                                    │
         ┌──────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Relationships & Constraints                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ 1. people(id) → embeddings(person_id)    [1:N]                    │
│    - One person can have multiple embeddings                       │
│    - CASCADE DELETE: Remove embeddings when person deleted         │
│                                                                     │
│ 2. people(id) → events(person_id)        [1:N]                    │
│    - One person can have multiple tracking events                  │
│    - NULL allowed: Events can exist without person (unknown)       │
│                                                                     │
│ 3. Indexes for Performance:                                        │
│    - people.name (UNIQUE)                                          │
│    - events.timestamp (ORDER BY optimization)                      │
│    - events.person_id (JOIN optimization)                          │
│    - embeddings.person_id (JOIN optimization)                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Query Optimization Patterns:**
```sql
-- Fast person lookup
SELECT * FROM people WHERE name = ? 

-- Embedding retrieval for recognition
SELECT vec FROM embeddings WHERE person_id = ?

-- Recent tracking events
SELECT * FROM events ORDER BY timestamp DESC LIMIT 100

-- Person statistics
SELECT COUNT(*) FROM events WHERE person_id = ? AND date(timestamp) = date('now')
```

#### 4. Real-time Processing Optimization
- **Frame Skipping**: Adaptive processing based on system load
- **Gallery Caching**: In-memory storage of known face embeddings
- **Multi-threading**: Separate threads for video processing and UI updates
- **Resource Management**: Memory-efficient track and detection management

### Mathematical Foundations

#### 1. Cosine Similarity
```
similarity = (A · B) / (||A|| × ||B||)
distance = 1 - similarity
```
Used for comparing face embeddings in high-dimensional space.

#### 2. Kalman Filter Equations
```
Prediction: x̂(k|k-1) = F·x̂(k-1|k-1) + B·u(k)
Update: x̂(k|k) = x̂(k|k-1) + K(k)·[z(k) - H·x̂(k|k-1)]
```
Used for tracking object motion and predicting future positions.

#### 3. Hungarian Algorithm
Solves the assignment problem with O(n³) complexity for optimal track-detection matching.

### Performance Characteristics
- **Frame Rate**: 15-30 FPS (hardware dependent)
- **Recognition Accuracy**: >95% under controlled conditions
- **Memory Usage**: <2GB for typical operation
- **Scalability**: Linear scaling up to 10,000 enrolled persons

---

## Burmese Version (မြန်မာဘာသာ)

### စီမံကိန်း အကြမ်းဖျင်း
FaceScannerPro သည် အဆင့်မြင့် အချိန်နှင့်တပြေးညီ မျက်နှာအမှတ်အသားပြုခြင်းနှင့် ခြေရာခံခြင်း စနစ်ဖြစ်ပြီး၊ ခေတ်မီ နက်နဲသော သင်ယူမှု မော်ဒယ်များနှင့် ထိရောက်သော ခြေရာခံ အယ်လဂိုရီသမ်များကို ပေါင်းစပ်ထားသည်။

### အဓိက နည်းပညာများနှင့် လိုင်ဘရေရီများ

#### ၁။ မျက်နှာအမှတ်အသား ပြုခြင်း ဘောင်
- **InsightFace (buffalo_l model)**
  - **ရည်ရွယ်ချက်**: အဓိက မျက်နှာအမှတ်အသားပြု အင်ဂျင်
  - **နည်းပညာ**: နက်နဲသော အာရုံကြောစိတ် ကွန်ယက်အခြေခံ မျက်နှာအမှတ်အသားပြုခြင်း
  - **မော်ဒယ်**: buffalo_l - ၅၁၂-အတိုင်းအတာ မျက်နှာ embedding များ
  - **သီအိုရီ**: ArcFace loss function - မျက်နှာ လက္ခဏာ သင်ယူမှု တိုးတက်စေရန်
  - **စွမ်းဆောင်ရည်**: စံ benchmark များတွင် ခေတ်မီ တိကျမှု
  - **အကောင်အထည်ဖော်မှု**: ONNX Runtime ဖြင့် အကောင်းဆုံး inference

#### ၂။ အရာဝတ္ထု ခြေရာခံ စနစ်
- **DeepSORT (Deep Simple Online and Realtime Tracking)**
  - **ရည်ရွယ်ချက်**: အများအပြား အရာဝတ္ထု ခြေရာခံခြင်း အချိန်ကြာမြင့် လိုက်လျောညီထွေရှိမှုဖြင့်
  - **အစိတ်အပိုင်းများ**:
    - Kalman Filter: လှုပ်ရှားမှု ကြိုတင်ခန့်မှန်းခြင်းနှင့် အခြေအနေ ခန့်မှန်းခြင်း
    - Hungarian Algorithm: detection များနှင့် track များအကြား အကောင်းဆုံး သတ်မှတ်ခြင်း
    - Deep Association Metric: အမွေအပြင် အခြေခံ ပြန်လည်သတ်မှတ်ခြင်း
  - **သီအိုရီ**: လှုပ်ရှားမှုနှင့် အမွေအပြင် အရိပ်အယောင်များကို ပေါင်းစပ်၍ ခိုင်မာသော ခြေရာခံခြင်း

#### ၃။ ကွန်ပျူတာ မြင်ကွင်း အခြေခံ
- **OpenCV (cv2)**
  - **ရည်ရွယ်ချက်**: ပုံ လုပ်ဆောင်ခြင်းနှင့် ဗီဒီယို ဖမ်းယူခြင်း
  - **လုပ်ဆောင်ချက်များ**: 
    - ဗီဒီယို I/O လုပ်ငန်းများ
    - ပုံ ကြိုတင်လုပ်ဆောင်ခြင်းနှင့် ပြောင်းလဲခြင်း
    - မှတ်စုများနှင့် အပေါ်ထပ်များ ရေးဆွဲခြင်း

#### ၄။ သင်္ချာ တွက်ချက်မှု
- **NumPy**
  - **ရည်ရွယ်ချက်**: ကိန်းဂဏန်း တွက်ချက်မှုများနှင့် array လုပ်ငန်းများ
  - **အသုံးပြုမှု**: 
    - Embedding vector လုပ်ငန်းများ
    - Cosine distance တွက်ချက်မှုများ
    - မျက်နှာ ညှိညွတ်မှုအတွက် matrix ကိုင်တွယ်မှုများ

#### ၅။ ဒေတာဘေ့စ် စီမံခန့်ခွဲမှု
- **SQLite3**
  - **ရည်ရွယ်ချက်**: လူပုဂ္ဂိုလ် ဒေတာများနှင့် embedding များ သိမ်းဆည်းရန် ပေါ့ပါး ဒေတာဘေ့စ်
  - **Schema**: 
    - People table: လူပုဂ္ဂိုလ် အချက်အလက် သိမ်းဆည်းမှု
    - Embeddings table: မျက်နှာ လက္ခဏာ vector များ
    - Events table: ခြေရာခံ သမိုင်းနှင့် မှတ်တမ်းများ

#### ၆။ အသုံးပြုသူ ကြားခံ ဘောင်
- **Tkinter with TTK**
  - **ရည်ရွယ်ချက်**: ခေတ်မီ desktop GUI application
  - **လက္ခဏာများ**:
    - Tab ကြားခံ ဒီဇိုင်း
    - အချိန်နှင့်တပြေးညီ ဗီဒီယို ပြသမှု
    - တုံ့ပြန်သော layout စီမံခန့်ခွဲမှု

### နည်းပညာ နည်းလမ်းများ

#### ၁။ မျက်နှာအမှတ်အသားပြု Pipeline
```
Input Frame → မျက်နှာ ရှာဖွေခြင်း → မျက်နှာ ညှိညွတ်ခြင်း → လက္ခဏာ ထုတ်ယူခြင်း → တူညီမှု ကိုက်ညီခြင်း → လူမှု သတ်မှတ်ခြင်း
```

#### ၂။ ခြေရာခံ အယ်လဂိုရီသမ်
```
ယခင် Track များ → လှုပ်ရှားမှု ကြိုတင်ခန့်မှန်းခြင်း → Detection ဆက်စပ်ခြင်း → Track အပ်ဒိတ်ခြင်း → လူမှု ထိန်းသိမ်းခြင်း
```

#### ၃။ ဒေတာဘေ့စ် ဗိသုကာ
```
Application Layer → Business Logic → Data Access Layer → SQLite Database
```

### သင်္ချာ အခြေခံများ

#### ၁။ Cosine Similarity
```
similarity = (A · B) / (||A|| × ||B||)
distance = 1 - similarity
```
အမြင့်-dimensional space တွင် မျက်နှာ embedding များ နှိုင်းယှဉ်ရန် အသုံးပြုသည်။

#### ၂။ Kalman Filter ညီမျှခြေများ
```
ကြိုတင်ခန့်မှန်းခြင်း: x̂(k|k-1) = F·x̂(k-1|k-1) + B·u(k)
အပ်ဒိတ်ခြင်း: x̂(k|k) = x̂(k|k-1) + K(k)·[z(k) - H·x̂(k|k-1)]
```
အရာဝတ္ထု လှုပ်ရှားမှု ခြေရာခံခြင်းနှင့် အနာဂတ် အနေအထား ကြိုတင်ခန့်မှန်းခြင်းအတွက် အသုံးပြုသည်။

#### ၃။ Hungarian Algorithm
O(n³) ရှုပ်ထွေးမှုဖြင့် အကောင်းဆုံး track-detection ကိုက်ညီမှုအတွက် assignment problem ကို ဖြေရှင်းသည်။

### စွမ်းဆောင်ရည် လက္ခဏာများ
- **Frame Rate**: ၁၅-၃၀ FPS (ဟာ့ဒ်ဝဲ ပေါ်မူတည်၍)
- **အမှတ်အသားပြု တိကျမှု**: ထိန်းချုပ်ထားသော အခြေအနေများတွင် >95%
- **မမ်မိုရီ အသုံးပြုမှု**: ပုံမှန် လုပ်ဆောင်မှုအတွက် <2GB
- **အတိုင်းအတာ ချဲ့နိုင်မှု**: ၁၀,၀၀၀ မှတ်ပုံတင်ထားသော လူများအထိ linear scaling

### လိုင်ဘရေရီများ စာရင်း
```python
# အဓိက လိုင်ဘရေရီများ
import cv2                    # OpenCV - ကွန်ပျူတာ မြင်ကွင်း
import numpy as np            # NumPy - သင်္ချာ တွက်ချက်မှု
import insightface            # InsightFace - မျက်နှာ အမှတ်အသားပြုမှု
import tkinter as tk          # Tkinter - GUI ဘောင်
import sqlite3               # SQLite - ဒေတာဘေ့စ်
import threading             # Threading - multi-threading
import time                  # Time - အချိန် လုပ်ငန်းများ
import os                    # OS - file system လုပ်ငန်းများ
import PIL                   # PIL - ပုံ လုပ်ဆောင်ခြင်း

# နောက်ထပ် လိုင်ဘရေရီများ
from deep_sort_realtime.deepsort_tracker import DeepSort  # DeepSORT tracking
import onnxruntime           # ONNX Runtime - ML inference
import logging               # Logging - မှတ်တမ်း ရေးသားမှု
```

### နိဂုံး
FaceScannerPro သည် ခေတ်မီ နည်းပညာများကို အသုံးပြု၍ တည်ဆောက်ထားသော အဆင့်မြင့် မျက်နှာအမှတ်အသားပြုခြင်းနှင့် ခြေရာခံခြင်း စနစ်ဖြစ်ပြီး၊ လက်တွေ့ အသုံးပြုမှုများအတွက် သင့်လျော်သော ရှုပ်ထွေးမှုနှင့် စွမ်းဆောင်ရည် လိုအပ်ချက်များကို ဟန်ချက်ညီစွာ ပေါင်းစပ်ထားသည်။

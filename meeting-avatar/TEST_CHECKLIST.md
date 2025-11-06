# Meeting Avatar Test Checklist

## Prerequisites
- [ ] OBS Studio installed and configured
- [ ] VB-Cable installed
- [ ] Zoom credentials in .env
- [ ] Virtual environment activated

## Component Tests

### 1. Avatar Display
- [ ] Run `python test_window.py`
- [ ] Avatar window appears
- [ ] Animation is smooth
- [ ] Window visible in OBS

### 2. Virtual Camera
- [ ] OBS Virtual Camera started
- [ ] Avatar visible in Windows Camera app
- [ ] Avatar visible in Zoom video settings

### 3. Audio Setup
- [ ] VB-Cable appears in Windows sound settings
- [ ] Audio routing works (test with `python test_audio.py`)
- [ ] No audio feedback loops

### 4. Zoom Integration
- [ ] Can authenticate with Zoom
- [ ] Can join test meeting
- [ ] Avatar appears in meeting
- [ ] Can capture meeting audio

### 5. Full System Test
- [ ] Run `python system_test.py`
- [ ] All components pass
- [ ] Schedule test meeting
- [ ] Avatar joins automatically
- [ ] Audio transcription works
# PRINTBENCH Camera Controls WIP

Status: preserved in Git because the BND Windows build PC was shut down before the local runtime patch could be applied and compiled.

Base commit before this WIP: `f546ab53` (`Make FINAL-MASTER navigation functional`).

## Binding target

The FINAL-MASTER camera card already uses the native `MediaPlayCtrl`/`wxMediaCtrl2` path and the P2S live LAN stream. The next change adds native PRINTBENCH camera controls directly below the player, without Bambu Studio and without a second camera stack.

Use the existing `MachineObject` LAN commands:

- `command_ipcam_record(bool on_off)`
- `command_ipcam_timelapse(bool on_off)`
- `command_ipcam_resolution_set(std::string resolution)`

Live state is already available through `PrintbenchSnapshot`:

- `has_camera`
- `camera_recording`
- `camera_timelapse`
- `camera_resolution`

## Intended native UI

Add these members to `PrintbenchNativePanel`:

```cpp
wxButton* m_camera_record{nullptr};
wxButton* m_camera_timelapse{nullptr};
wxButton* m_camera_resolution{nullptr};
```

In the `LIVE KAMERA` card, below `m_media_play_ctrl`, add a horizontal button row:

```cpp
auto* camera_controls = new wxBoxSizer(wxHORIZONTAL);
m_camera_record = new wxButton(camera_card, wxID_ANY, "AUFNAHME");
m_camera_timelapse = new wxButton(camera_card, wxID_ANY, "TIMELAPSE");
m_camera_resolution = new wxButton(camera_card, wxID_ANY, "AUFLOESUNG");
for (auto* button : {m_camera_record, m_camera_timelapse, m_camera_resolution}) {
    button->SetMinSize(wxSize(FromDIP(90), FromDIP(30)));
    button->SetBackgroundColour(wxColour("#0B2639"));
    button->SetForegroundColour(*wxWHITE);
    button->Enable(false);
    camera_controls->Add(button, 1, button == m_camera_resolution ? 0 : wxRIGHT, FromDIP(6));
}
body->Add(camera_controls, 0, wxEXPAND | wxTOP, FromDIP(6));
```

Bind controls to the connected `MachineObject`:

```cpp
m_camera_record->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
    if (m_machine && m_machine->is_connected() && m_machine->has_ipcam)
        m_machine->command_ipcam_record(!m_machine->camera_recording);
});

m_camera_timelapse->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
    if (m_machine && m_machine->is_connected() && m_machine->has_ipcam)
        m_machine->command_ipcam_timelapse(!m_machine->camera_timelapse);
});

m_camera_resolution->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
    if (!m_machine || !m_machine->is_connected() || !m_machine->has_ipcam)
        return;
    const auto& supported = m_machine->camera_resolution_supported;
    if (supported.empty())
        return;
    auto it = std::find(supported.begin(), supported.end(), m_machine->camera_resolution);
    size_t next = it == supported.end() ? 0 : (static_cast<size_t>(std::distance(supported.begin(), it)) + 1) % supported.size();
    m_machine->command_ipcam_resolution_set(supported[next]);
});
```

Update the button state in `apply_snapshot()`:

```cpp
const bool camera_ready = connected && s.has_camera;
if (m_camera_record) {
    m_camera_record->Enable(camera_ready);
    m_camera_record->SetLabel(s.camera_recording ? "AUFNAHME AUS" : "AUFNAHME");
    m_camera_record->SetBackgroundColour(s.camera_recording ? wxColour("#651B2A") : wxColour("#0B2639"));
}
if (m_camera_timelapse) {
    m_camera_timelapse->Enable(camera_ready);
    m_camera_timelapse->SetLabel(s.camera_timelapse ? "TIMELAPSE AUS" : "TIMELAPSE");
    m_camera_timelapse->SetBackgroundColour(s.camera_timelapse ? wxColour("#075C46") : wxColour("#0B2639"));
}
if (m_camera_resolution) {
    m_camera_resolution->Enable(camera_ready && m_machine && !m_machine->camera_resolution_supported.empty());
    m_camera_resolution->SetLabel(s.camera_resolution.empty() ? "AUFLOESUNG" : wxString::FromUTF8(s.camera_resolution));
}
```

## Validation to perform when a Windows builder is available

1. Run product contract and pytest suite.
2. Build fresh Windows EXE/DLL.
3. Launch against the real P2S on LAN.
4. Verify camera stream still starts automatically.
5. Toggle recording and confirm live snapshot state follows.
6. Toggle timelapse and confirm live snapshot state follows.
7. Cycle only values reported by `camera_resolution_supported`.
8. Capture FINAL-MASTER comparison screenshot.
9. Commit source changes only after the real Windows build passes.

No Bambu Studio dependency is to be introduced. JL1976 branding and the binding FINAL-MASTER remain mandatory.
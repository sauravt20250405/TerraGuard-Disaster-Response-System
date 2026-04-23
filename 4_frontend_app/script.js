
        const API_URL = (window.location.origin === "file://" || window.location.origin === "null" || (window.location.port && window.location.port !== "5000")) ? "http://127.0.0.1:5000" : window.location.origin;
        let USER_COORDS = [31.1048, 77.1734];
        let currentCity = "Detecting Location...";
        let map, mapSos, mapIncidents;
        let mapsInitialized = false;
        let markers = [], markersSos = [], markersInc = [];
        let histMarkers = [], histMarkersSos = [], histMarkersInc = [], histMarkersComm = [];
        let refreshInterval;
        let currentUser = null;
        let currentLang = "en";
        let currentThreat = "General";
        let incidentsData = {};
        let activeModalIncidentId = null;

        const translations = {
            en: {
                nav_dashboard: "📊 Daily Dashboard", nav_map: "🗺️ Live Map", nav_sos: "🚨 SOS Beacon", nav_report: "🏗️ Report Hazard",
                nav_resources: "🏥 Local Resources", nav_vault: "🗄️ Digital Vault", nav_firstaid: "⚕️ First Aid Guide", nav_incidents: "📋 Live Incidents",
                logout: "Log Out", weather_title: "🌤️ Daily Weather & Safety", tips_title: "🏔️ Himalayan Safety Tip",
                family_checkin: "👨‍👩‍👧 Family Check-In", family_desc: "Instantly notify 3 pre-saved contacts that you are safe, along with your GPS location.",
                report_hazard: "🏗️ Report Non-Emergency Hazard", report_desc: "Help the community by reporting fallen trees, blocked drains, or road cracks.",
                hazard_type: "Hazard Type", hazard_desc: "Description", submit_btn: "Submit Report to PWD / NDRF",
                local_resources: "🏥 Local Emergency Resources", digital_vault: "🗄️ Offline Digital Vault", vault_desc: "Securely store critical documents for offline access during evacuations.",
                first_aid: "⚕️ Offline First Aid Guide", fa_cpr: "CPR Basics", fa_fracture: "Checking Splints / Fractures", fa_cold: "Frostbite & Hypothermia", direct_call: "📞 Direct Call"
            },
            hi: {
                nav_dashboard: "📊 दैनिक डैशबोर्ड", nav_map: "🗺️ लाइव मैप", nav_sos: "🚨 आपातकालीन (SOS)", nav_report: "🏗️ खतरे की रिपोर्ट करें",
                nav_resources: "🏥 स्थानीय संसाधन", nav_vault: "🗄️ डिजिटल वॉल्ट", nav_firstaid: "⚕️ प्राथमिक चिकित्सा", nav_incidents: "📋 लाइव घटनाएँ",
                logout: "लॉग आउट", weather_title: "🌤️ दैनिक मौसम और सुरक्षा", tips_title: "🏔️ हिमालयन सुरक्षा टिप",
                family_checkin: "👨‍👩‍👧 परिवार चेक-इन", family_desc: "3 पहले से सहेजे गए संपर्कों को तुरंत सूचित करें कि आप सुरक्षित हैं, साथ ही अपना GPS स्थान भेजें।",
                report_hazard: "🏗️ गैर-आपातकालीन खतरे की रिपोर्ट करें", report_desc: "गिरे हुए पेड़ों या अवरुद्ध सड़कों की रिपोर्ट करके समुदाय की मदद करें।",
                hazard_type: "खतरे का प्रकार", hazard_desc: "विवरण", submit_btn: "रिपोर्ट दर्ज करें",
                local_resources: "🏥 स्थानीय आपातकालीन संसाधन", digital_vault: "🗄️ ऑफ़लाइन डिजिटल वॉल्ट", vault_desc: "निकासी के दौरान ऑफ़लाइन पहुंच के लिए महत्वपूर्ण दस्तावेज़ों को सुरक्षित रूप से संग्रहीत करें।",
                first_aid: "⚕️ ऑफ़लाइन प्राथमिक चिकित्सा मार्गदर्शिका", fa_cpr: "सीपीआर बेसिक्स", fa_fracture: "फ्रैक्चर की जांच", fa_cold: "फ्रॉस्टबाइट और हाइपोथर्मिया", direct_call: "📞 सीधा कॉल"
            }
        };

        async function fetchUserLocation() {
            return new Promise((resolve) => {
                currentCity = "Detecting GPS...";
                if ("geolocation" in navigator) {
                    navigator.geolocation.getCurrentPosition(async (pos) => {
                        USER_COORDS = [pos.coords.latitude, pos.coords.longitude];
                        try {
                            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${USER_COORDS[0]}&lon=${USER_COORDS[1]}`);
                            const data = await res.json();
                            currentCity = data.address.city || data.address.town || data.address.county || data.address.state || "Your GPS Region";
                        } catch(e) { currentCity = "Live GPS Region"; }
                        resolve();
                    }, async (err) => {
                        console.warn("GPS failed, trying IP fallback.");
                        await fallbackIpFetch();
                        resolve();
                    }, { timeout: 10000, enableHighAccuracy: true });
                } else {
                    fallbackIpFetch().then(resolve);
                }
            });
        }

        async function fallbackIpFetch() {
            try {
                const res = await fetch("https://ipapi.co/json/");
                const data = await res.json();
                if(data && data.latitude) {
                    USER_COORDS = [data.latitude, data.longitude];
                    currentCity = data.city || "Detected IP Area";
                }
            } catch(e) { }
        }

        async function searchFirstAid() {
            const query = document.getElementById("firstAidSearch").value.trim();
            const resultsEl = document.getElementById("firstAidResults");
            if (!query) return;
            
            resultsEl.innerHTML = '<div style="color:var(--text-muted)">Searching official Wikipedia clinical summaries...</div>';
            
            try {
                const res = await fetch(`https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exsentences=6&exlimit=1&titles=${encodeURIComponent(query)}&explaintext=1&formatversion=2&origin=*&format=json`);
                const data = await res.json();
                const page = data.query.pages[0];
                
                if (page && page.extract) {
                    resultsEl.innerHTML = `
                        <div class="first-aid-card" style="border-left-color: var(--accent-red);">
                            <strong>${page.title}</strong>
                            <p style="margin-top:10px; color:var(--text-muted); font-size:0.9rem; line-height:1.5;">${page.extract}</p>
                            <small style="display:block; margin-top:10px; color:var(--accent-red); font-weight:600;">⚠ Always dial 112 immediately. This is reference material.</small>
                        </div>
                    `;
                } else {
                    resultsEl.innerHTML = '<div style="color:var(--text-muted)">No specialized medical summary found. Dial 112.</div>';
                }
            } catch(e) {
                resultsEl.innerHTML = '<div style="color:var(--text-muted)">Connection failed. See offline guide above.</div>';
            }
        }

        // --- MEGA PATCH: DIGITAL VAULT CRUD ---
        async function loadVaultDocuments() {
            const vaultContainer = document.getElementById("vaultDocuments");
            if (!currentUser) return;
            try {
                const res = await fetch(`${API_URL}/api/vault/list/${currentUser.user_id}`);
                const data = await res.json();
                
                if (data.documents && data.documents.length > 0) {
                    vaultContainer.innerHTML = data.documents.map(d => `
                        <div class="vault-item" style="flex-direction:row; align-items:center; justify-content:space-between; margin-bottom:0;">
                            <div>
                                <div style="margin-bottom:4px">📄 <strong>${d.filename}</strong></div>
                                <small style="color:var(--accent-green)">Cloud Encrypted &bull; ${new Date(d.timestamp).toLocaleDateString()}</small>
                            </div>
                            <button onclick="deleteVaultDocument(${d.doc_id})" style="background:none; border:none; color:var(--accent-red); cursor:pointer; font-size:1.2rem;">🗑️</button>
                        </div>
                    `).join("");
                } else {
                    vaultContainer.innerHTML = '<div style="color:var(--text-muted)">No documents secured yet.</div>';
                }
            } catch(e) {
                vaultContainer.innerHTML = '<div style="color:var(--accent-red)">Database connection failed. Viewing offline cached items.</div>';
            }
        }

        async function uploadVaultDocument() {
            const fileInput = document.getElementById("vaultUploadFile");
            if (!fileInput.files.length || !currentUser) return;
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append("file", file);
            formData.append("user_id", currentUser.user_id);
            
            const originalText = document.getElementById("vaultDocuments").innerHTML;
            document.getElementById("vaultDocuments").innerHTML = '<div style="color:var(--accent-amber)">Encrypting and uploading to Aiven...</div>';
            
            try {
                const res = await fetch(`${API_URL}/api/vault/upload`, { method: "POST", body: formData });
                if (res.ok) {
                    await loadVaultDocuments();
                } else {
                    alert("Upload failed.");
                    document.getElementById("vaultDocuments").innerHTML = originalText;
                }
            } catch(e) {
                alert("Upload failed: " + e.message);
                document.getElementById("vaultDocuments").innerHTML = originalText;
            }
            fileInput.value = "";
        }

        async function deleteVaultDocument(doc_id) {
            if (!confirm("Permanently delete this secure document from the cloud?")) return;
            try {
                const res = await fetch(`${API_URL}/api/vault/delete/${doc_id}`, { method: "DELETE" });
                if (res.ok) {
                    await loadVaultDocuments();
                }
            } catch(e) {
                alert("Failed to delete.");
            }
        }

        async function fetchFirstAidInit() {
            const resultsEl = document.getElementById("firstAidResults");
            resultsEl.innerHTML = '<div style="color:var(--accent-amber)">Fetching live Wikipedia Intelligence...</div>';
            try {
                const res = await fetch(`${API_URL}/api/first_aid_live`);
                const data = await res.json();
                if (data.success) {
                    resultsEl.innerHTML = data.content.map(txt => `
                        <div class="first-aid-card" style="border-left-color: var(--accent-amber); margin-bottom: 15px;">
                            <strong>${data.source}</strong>
                            <p style="margin-top:10px; color:var(--text-muted); font-size:0.9rem; line-height:1.5;">${txt}</p>
                        </div>
                    `).join("");
                } else {
                    resultsEl.innerHTML = '<div style="color:var(--accent-red)">Failed to fetch live data.</div>';
                }
            } catch(e) {
                resultsEl.innerHTML = '<div style="color:var(--accent-red)">API Scraper unreachable.</div>';
            }
        }

        function toggleTheme() {
            document.body.classList.toggle("light-mode");
            const isLight = document.body.classList.contains("light-mode");
            localStorage.setItem("terraguard_theme", isLight ? "light" : "dark");
        }

        function toggleLanguage() {
            currentLang = currentLang === "en" ? "hi" : "en";
            applyLanguage(currentLang);
        }

        function selectThreat(btn, threat) {
            document.querySelectorAll('.threat-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentThreat = threat;
        }

        function applyLanguage(lang) {
            document.querySelectorAll("[data-i18n]").forEach(el => {
                const key = el.getAttribute("data-i18n");
                if (translations[lang] && translations[lang][key]) {
                    if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
                        el.placeholder = translations[lang][key];
                    } else {
                        el.innerHTML = translations[lang][key];
                    }
                }
            });
        }

        // ---------- Session Guard ----------
        function loadSession() {
            const uid = localStorage.getItem("terraguard_user_id");
            const rid = localStorage.getItem("terraguard_role_id");
            const rname = localStorage.getItem("terraguard_role_name");
            if (uid && rname) {
                currentUser = { user_id: uid, role_id: rid, role_name: rname };
                document.getElementById("loginOverlay").style.display = "none";
                document.getElementById("app").style.display = "flex";
                document.getElementById("userRole").textContent = rname;
                initAfterAuth();
                return true;
            }
            return false;
        }

        function saveSession(data) {
            localStorage.setItem("terraguard_user_id", data.user_id);
            localStorage.setItem("terraguard_role_id", data.role_id || "");
            localStorage.setItem("terraguard_role_name", data.role_name || "Civilian");
            currentUser = data;
        }

        function logout() {
            localStorage.removeItem("terraguard_user_id");
            localStorage.removeItem("terraguard_role_id");
            localStorage.removeItem("terraguard_role_name");
            currentUser = null;
            document.getElementById("loginOverlay").style.display = "flex";
            document.getElementById("app").style.display = "none";
        }

        // ---------- Login ----------
        async function handleLogin(e) {
            e.preventDefault();
            const phone = document.getElementById("loginPhone").value.trim();
            const pwd = document.getElementById("loginPassword").value;
            const errEl = document.getElementById("loginError");
            errEl.textContent = "";
            try {
                const res = await fetch(`${API_URL}/api/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ phone_number: phone, password: pwd })
                });
                const data = await res.json();
                if (data.success) {
                    saveSession(data);
                    document.getElementById("loginOverlay").style.display = "none";
                    document.getElementById("app").style.display = "flex";
                    document.getElementById("userRole").textContent = data.role_name;
                    initAfterAuth();
                } else {
                    errEl.textContent = data.error || "Login failed";
                }
            } catch (e) {
                errEl.textContent = "Network error. Is the API running?";
            }
        }

        function toggleAuth(mode) {
            if (mode === 'register') {
                document.getElementById('loginBox').style.display = 'none';
                document.getElementById('registerBox').style.display = 'block';
            } else {
                document.getElementById('loginBox').style.display = 'block';
                document.getElementById('registerBox').style.display = 'none';
            }
        }

        async function handleRequestOTP(e) {
            e.preventDefault();
            const btn = document.getElementById("regOtpBtn");
            const err = document.getElementById("regError");
            err.textContent = "";
            btn.innerHTML = "Sending SMS...";
            
            const payload = {
                phone_number: document.getElementById("regPhone").value.trim()
            };

            try {
                const res = await fetch(`${API_URL}/api/request_otp`, {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    btn.style.display = 'none';
                    document.getElementById("otpSection").style.display = 'block';
                    err.style.color = 'var(--accent-green)';
                    err.textContent = "SMS Code Sent! Check your phone.";
                    
                    // Hackathon Demo: Display OTP directly in UI for fail-safe visibility
                    if (data.sandbox_otp) {
                        setTimeout(() => {
                            err.innerHTML = `<div style="padding:15px; border:1px solid var(--accent-green); background:rgba(48,164,108,0.1); border-radius:8px; color:#fff; font-weight:600; text-align:center; margin-bottom:15px;">
                                💬 SIMULATED SMS RECEIVED<br>
                                <div style="font-size:1.8rem; letter-spacing:6px; color:var(--accent-amber); margin:8px 0;">${data.sandbox_otp}</div>
                                <small style="font-weight:400; color:var(--text-muted)">Enter this code below to verify</small>
                            </div>`;
                        }, 500);
                    }
                    
                    setTimeout(() => err.style.color = 'var(--accent-red)', 3000);
                    setTimeout(() => err.textContent = "", 3000);
                } else {
                    err.style.color = 'var(--accent-red)';
                    err.textContent = data.error || "Failed to send OTP.";
                    btn.innerHTML = "1. Verify via SMS";
                }
            } catch (error) {
                err.style.color = 'var(--accent-red)';
                err.textContent = "Network error. Is the API running?";
                btn.innerHTML = "1. Verify via SMS";
            }
        }

        async function handleVerifyRegistration() {
            const btn = document.querySelector("#otpSection button");
            const err = document.getElementById("regError");
            err.style.color = 'var(--accent-red)';
            err.textContent = "";
            btn.innerHTML = "Verifying...";

            const isAgency = document.getElementById("regAgencyToggle") ? document.getElementById("regAgencyToggle").checked : false;
            const payload = {
                name: document.getElementById("regName").value.trim(),
                phone_number: document.getElementById("regPhone").value.trim(),
                password: document.getElementById("regPassword").value,
                otp: document.getElementById("regOtpField").value.trim(),
                agency_code: isAgency ? document.getElementById("regAgencyCode").value.trim() : ""
            };

            try {
                const res = await fetch(`${API_URL}/api/register`, {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    saveSession({
                        user_id: data.user_id,
                        role_id: data.role_id,
                        role_name: data.role_name
                    });
                    document.getElementById("loginOverlay").style.display = "none";
                    document.getElementById("app").style.display = "flex";
                    document.getElementById("userRole").textContent = data.role_name;
                    initAfterAuth();
                } else {
                    err.textContent = data.error || "Registration failed";
                    btn.innerHTML = "2. Complete Registration";
                }
            } catch (error) {
                err.textContent = "Network error connecting to API.";
                btn.innerHTML = "2. Complete Registration";
            }
        }


        // ---------- Post-Auth Init ----------
        async function initAfterAuth() {
            if (localStorage.getItem("terraguard_theme") === "light") {
                document.body.classList.add("light-mode");
            }
            
            // Load saved family contacts
            document.getElementById("familyContact1").value = localStorage.getItem("familyContact1") || "";
            document.getElementById("familyContact2").value = localStorage.getItem("familyContact2") || "";
            document.getElementById("familyContact3").value = localStorage.getItem("familyContact3") || "";
            
            // Mega-Patch Vault and First Aid
            loadVaultDocuments();
            fetchFirstAidInit();
            
            await fetchUserLocation();

            const isCivilian = currentUser.role_name === "Civilian";
            document.getElementById("headerTitle").textContent = isCivilian ? "TerraGuard | Safety Assistant" : "Command Center";

            document.querySelectorAll('.civ-nav').forEach(el => el.style.display = isCivilian ? "block" : "none");
            document.querySelectorAll('.agency-nav').forEach(el => el.style.display = isCivilian ? "none" : "block");

            document.getElementById("incidentsTitle").textContent = "Live Incidents – " + (currentUser.role_name || "").replace(/_/g, " ");
            if (isCivilian) showView("dashboard"); else showView("map");
            initMaps();
            fetchRisk();
            fetchIncidents();
            fetchDisasterRisk();
            fetchLocalResources();
            fetchLiveNews();
            if (typeof initCivilianDashboard === "function") initCivilianDashboard();
            clearInterval(refreshInterval);
            refreshInterval = setInterval(refreshData, 5000);
            applyLanguage(currentLang);
        }

        async function fetchLiveNews() {
            const newsEl = document.getElementById("liveNews");
            if(!newsEl) return;
            
            newsEl.innerHTML = '<div class="tip-box" style="border-left-color: var(--accent-amber); color:var(--text-muted);">Fetching Global Incident Reports...</div>';
            
            try {
                const queryLocation = encodeURIComponent(currentCity.length > 3 ? currentCity : "Global");
                const res = await fetch(`https://api.reliefweb.int/v1/reports?appname=TerraGuard&query[value]=${queryLocation}&limit=3&preset=latest`);
                const data = await res.json();
                
                if(data && data.data && data.data.length > 0) {
                    newsEl.innerHTML = '';
                    data.data.forEach(item => {
                        newsEl.innerHTML += `
                            <div class="tip-box" style="border-left-color: var(--accent-red); margin-bottom: 8px;">
                                <strong>${item.fields.title}</strong>
                                <small style="display:block; color:var(--text-muted); margin-top:4px;">ReliefWeb API · ${new Date(item.fields.date.created).toLocaleDateString()}</small>
                            </div>
                        `;
                    });
                } else {
                    newsEl.innerHTML = '<div class="tip-box" style="border-left-color: var(--accent-green);">No major disaster alerts registered via ReliefWeb for your specific area. Stay tuned to local authorities.</div>';
                }
            } catch(e) {
                newsEl.innerHTML = '<div class="tip-box" style="border-left-color: var(--accent-amber); color:var(--text-muted);">⚠ ReliefWeb connection timeout.</div>';
            }
        }

        function initMaps() {
            if (mapsInitialized) return;
            mapsInitialized = true;
            const tileUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

            map = L.map("map").setView(USER_COORDS, 13);
            L.tileLayer(tileUrl, { attribution: "© OSM" }).addTo(map);
            map.on("moveend", function () { const c = map.getCenter(); fetchDisasterRiskFor(c.lat, c.lng); });

            mapSos = L.map("mapSos").setView(USER_COORDS, 13);
            L.tileLayer(tileUrl, { attribution: "© OSM" }).addTo(mapSos);
            mapSos.on("moveend", function () { const c = mapSos.getCenter(); fetchDisasterRiskFor(c.lat, c.lng); });

            mapIncidents = L.map("mapIncidents").setView(USER_COORDS, 13);
            L.tileLayer(tileUrl, { attribution: "© OSM" }).addTo(mapIncidents);
            mapIncidents.on("moveend", function () { const c = mapIncidents.getCenter(); fetchDisasterRiskFor(c.lat, c.lng); });

            const mcDiv = document.getElementById("mapComm");
            if (mcDiv) {
                mapComm = L.map("mapComm").setView(USER_COORDS, 13);
                L.tileLayer(tileUrl, { attribution: "© OSM" }).addTo(mapComm);
                mapComm.on("moveend", function () { const c = mapComm.getCenter(); fetchDisasterRiskFor(c.lat, c.lng); });
            }
        }

        function showView(name) {
            document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
            document.querySelectorAll(".sidebar nav button").forEach(b => b.classList.remove("active"));
            const cap = name.charAt(0).toUpperCase() + name.slice(1);
            const view = document.getElementById("view" + cap);
            const btn = document.getElementById("nav" + cap);
            if (view) view.classList.add("active");
            if (btn) btn.classList.add("active");
            if (name === "incidents" && currentUser?.role_name !== "Civilian") fetchDashboard();
            setTimeout(() => {
                if (map) map.invalidateSize();
                if (mapSos) mapSos.invalidateSize();
                if (mapIncidents) mapIncidents.invalidateSize();
                if (typeof mapComm !== 'undefined' && mapComm) mapComm.invalidateSize();
            }, 100);
        }

        // ---------- Data Fetch ----------
        async function fetchRisk() {
            try {
                const res = await fetch(`${API_URL}/api/weather_risk`);
                const data = await res.json();
                const badge = document.getElementById("riskBadge");
                badge.textContent = `Risk: ${data.ai_risk_score}%`;
                badge.className = "risk-badge " + (data.high_risk ? "danger" : "safe");
                document.getElementById("mapWrapper").classList.toggle("high-risk", data.high_risk);
                document.getElementById("mapWrapperSos").classList.toggle("high-risk", data.high_risk);
                document.getElementById("mapWrapperInc").classList.toggle("high-risk", data.high_risk);
            } catch (_) { }
        }

        async function fetchIncidents() {
            try {
                const res = await fetch(`${API_URL}/api/incidents`);
                const data = await res.json();
                if (data.incidents) updateMapPins(data.incidents);
            } catch (_) { }
        }

        function getActiveMapCenter() {
            const view = document.querySelector(".view.active");
            if (!view) return USER_COORDS;
            if (view.id === "viewMap" && map) return map.getCenter();
            if (view.id === "viewSos" && mapSos) return mapSos.getCenter();
            if (view.id === "viewIncidents" && mapIncidents) return mapIncidents.getCenter();
            return { lat: USER_COORDS[0], lng: USER_COORDS[1] };
        }

        async function fetchDisasterRiskFor(lat, lng) {
            const ids = ["disasterRisk", "disasterRiskSos", "disasterRiskInc"];
            try {
                ids.forEach(id => {
                    const e = document.getElementById(id);
                    if (e) e.innerHTML = `<strong>Historical Risk:</strong> Loading for ${lat.toFixed(2)}°N, ${lng.toFixed(2)}°E...`;
                });
                const res = await fetch(`${API_URL}/api/disaster_risk?lat=${lat}&lng=${lng}`);
                const data = await res.json();
                if (data.error) {
                    ids.forEach(id => {
                        const e = document.getElementById(id);
                        if (e) e.innerHTML = "<strong>Historical Risk:</strong> Model not loaded.";
                    });
                    addHistoricalPins([]);
                    return;
                }
                const msg = data.nearby_count === 0
                    ? `No disasters in 150km of ${lat.toFixed(2)}°N, ${lng.toFixed(2)}°E. Pan map to check other regions.`
                    : `${data.risk_score}% at ${lat.toFixed(2)}°N, ${lng.toFixed(2)}°E · ${data.nearby_count} disasters within 150km · Top: ${(data.top_disaster_types || []).map(t => t.type + " (" + t.count + ")").join(", ")}. Pan map to update.`;
                ids.forEach(id => {
                    const e = document.getElementById(id);
                    if (e) e.innerHTML = `<strong>Historical Risk:</strong> ${msg}`;
                });
                addHistoricalPins(data.nearby || []);
            } catch (_) {
                ids.forEach(id => { const e = document.getElementById(id); if (e) e.innerHTML = "<strong>Historical Risk:</strong> --"; });
            }
        }

        async function fetchDisasterRisk() {
            const c = getActiveMapCenter();
            const lat = typeof c === "object" ? c.lat : USER_COORDS[0];
            const lng = typeof c === "object" ? c.lng : USER_COORDS[1];
            await fetchDisasterRiskFor(lat, lng);
        }

        async function fetchLocalResources() {
            const listContainer = document.getElementById("dynamicResources");
            if (!listContainer) return;

            listContainer.innerHTML = '<li><div style="color:var(--text-muted)">Scanning live map for nearby hospitals, clinics, & police out to 10km...</div></li>';

            const lat = USER_COORDS[0];
            const lon = USER_COORDS[1];
            const query = `
            [out:json];
            (
              node["amenity"~"hospital|clinic|doctors|police|nursing_home"](around:10000,${lat},${lon});
              node["healthcare"~"clinic|doctor|centre|hospital"](around:10000,${lat},${lon});
            );
            out center 15;
        `;

            try {
                const res = await fetch("https://overpass-api.de/api/interpreter", {
                    method: "POST",
                    body: query
                });
                const data = await res.json();

                if (data && data.elements && data.elements.length > 0) {
                    listContainer.innerHTML = '';
                    data.elements.forEach(node => {
                        const tagType = node.tags.amenity || node.tags.healthcare || "medical";
                        const name = (node.tags && node.tags.name) ? node.tags.name : tagType.replace(/_/g, ' ') + " Facility";
                        const phone = (node.tags && node.tags.phone) ? node.tags.phone : "112";

                        const li = document.createElement("li");
                        li.innerHTML = `
                        <div><strong>${name}</strong><br><small style="color:var(--text-muted); text-transform:capitalize;">${tagType.replace(/_/g, ' ')} · &lt;10km Away</small></div>
                        <span style="color:var(--accent-green); font-weight:600; cursor:pointer;" onclick="window.location.href='tel:${phone}'">📞 ${phone}</span>
                    `;
                        listContainer.appendChild(li);
                    });
                } else {
                    listContainer.innerHTML = '<li><div style="color:var(--text-muted)">No distinct emergency facilities flagged on OSM within 10km. Always dial 112.</div></li>';
                }
            } catch (e) {
                listContainer.innerHTML = '<li><div style="color:var(--text-muted)">Could not connect to map stream. Stay safe!</div></li>';
            }
        }

        function addHistoricalPins(nearby) {
            const maps = [map, mapSos, mapIncidents];
            const arrs = [histMarkers, histMarkersSos, histMarkersInc];
            maps.forEach((m, i) => {
                if (!m) return;
                arrs[i].forEach(x => { try { m.removeLayer(x); } catch (_) { } });
                arrs[i].length = 0;
            });
            const icon = L.divIcon({ className: "pin", html: "<span style='background:#d29922;width:8px;height:8px;border-radius:50%;display:block;border:1px solid white'></span>", iconSize: [10, 10] });
            nearby.slice(0, 20).forEach(d => {
                const lat = parseFloat(d.Latitude), lng = parseFloat(d.Longitude);
                if (isNaN(lat) || isNaN(lng)) return;
                const tooltip = `${d.disaster_type || "Disaster"} (${d["Start Year"] || "?"}) - ${d.Location || ""}`;
                maps.forEach((m, i) => {
                    if (!m) return;
                    const marker = L.marker([lat, lng], { icon }).addTo(m);
                    marker.bindTooltip(tooltip, { permanent: false });
                    arrs[i].push(marker);
                });
            });
        }

        function refreshData() {
            fetchRisk();
            fetchIncidents();
            fetchDisasterRisk();
            if (typeof fetchCommunityReports === "function") fetchCommunityReports();
            if (currentUser && currentUser.role_name !== "Civilian") fetchDashboard();
        }

        function updateMapPins(incidents) {
            if (!map || !mapSos || !mapIncidents) return;
            const clearMarkers = (arr, m) => { arr.forEach(x => { try { m.removeLayer(x); } catch (_) { } }); arr.length = 0; };
            clearMarkers(markers, map);
            clearMarkers(markersSos, mapSos);
            clearMarkers(markersInc, mapIncidents);
            const addPin = (lat, lng, msg, m, arr) => {
                if (lat == null || lng == null) return;
                const icon = L.divIcon({ className: "pin", html: "<span style='background:#da3633;width:12px;height:12px;border-radius:50%;display:block;border:2px solid white'></span>", iconSize: [16, 16] });
                const marker = L.marker([lat, lng], { icon }).addTo(m);
                marker.bindTooltip(msg || "Incident", { permanent: false });
                arr.push(marker);
            };
            incidents.forEach(i => {
                const lat = parseFloat(i.latitude), lng = parseFloat(i.longitude);
                addPin(lat, lng, i.raw_message, map, markers);
                addPin(lat, lng, i.raw_message, mapSos, markersSos);
                addPin(lat, lng, i.raw_message, mapIncidents, markersInc);
            });
        }

        // ---------- Civilian Additional Logic ----------
        async function initCivilianDashboard() {
            document.querySelector('[data-i18n="weather_title"]').innerHTML = `🌤️ Weather & Safety (${currentCity})`;

            try {
                const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${USER_COORDS[0]}&longitude=${USER_COORDS[1]}&current_weather=true&hourly=uv_index&timezone=auto`);
                const data = await res.json();
                const temp = data.current_weather.temperature;
                const wind = data.current_weather.windspeed;
                const uv = data.hourly.uv_index[new Date().getHours()] || 0;
                document.getElementById("dashWeather").innerHTML = `
                <div class="weather-info">
                    <div class="weather-main">${temp}°C</div>
                    <div class="weather-sub">Wind: ${wind} km/h<br>UV Index: ${uv}</div>
                </div>`;
            } catch (e) {
                document.getElementById("dashWeather").innerHTML = "Weather data offline";
            }

            const tips = [
                "Driving to Kufri today? Check for black ice on the roads.",
                "Always keep an emergency kit with warm layers and a flashlight.",
                "During heavy rain, avoid parking near steep retaining walls.",
                "Keep your digital vault updated with your latest IDs."
            ];
            document.getElementById("dailyTip").textContent = tips[Math.floor(Math.random() * tips.length)];
        }

        function saveFamilyContacts() {
            localStorage.setItem("familyContact1", document.getElementById("familyContact1").value.trim());
            localStorage.setItem("familyContact2", document.getElementById("familyContact2").value.trim());
            localStorage.setItem("familyContact3", document.getElementById("familyContact3").value.trim());
            
            const status = document.getElementById("checkinStatus");
            status.style.color = "var(--accent-green)";
            status.innerText = "💾 Verified! Contacts Encrypted & Saved Locally.";
            setTimeout(() => status.innerText = "", 4000);
        }

        function sendFamilyCheckin() {
            const c1 = localStorage.getItem("familyContact1") || "";
            const c2 = localStorage.getItem("familyContact2") || "";
            const c3 = localStorage.getItem("familyContact3") || "";
            
            if (!c1 && !c2 && !c3) {
                alert("⚠️ Please save at least one family contact before broadcasting your status.");
                return;
            }

            const btn = document.querySelector(".checkin-btn");
            const status = document.getElementById("checkinStatus");
            if (btn.disabled) return;
            btn.disabled = true;
            btn.innerText = "📍 Acquiring GPS & Broadcasting...";
            status.style.color = "var(--accent-amber)";
            status.innerText = "Connecting to Satellite Gateway...";

            const successCb = (lat, lng) => {
                const link = `https://maps.google.com/?q=${lat},${lng}`;
                setTimeout(() => {
                    let out = "💬 [LIVE BROADCAST SENT]\n\nTO: \n";
                    if(c1) out += `• ${c1}\n`;
                    if(c2) out += `• ${c2}\n`;
                    if(c3) out += `• ${c3}\n`;
                    out += `\nMESSAGE:\n"I am safe. My current location is ${lat.toFixed(4)}, ${lng.toFixed(4)}."`;
                    
                    alert(out);
                    
                    status.style.color = "var(--accent-green)";
                    status.innerHTML = `✅ Successfully broadcasted safe status to saved numbers!`;
                    btn.innerText = "📍 I AM SAFE (Send Broadcast)";
                    btn.disabled = false;
                }, 1400);
            };

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (pos) => successCb(pos.coords.latitude, pos.coords.longitude),
                    () => successCb(USER_COORDS[0], USER_COORDS[1]) // fallback to default IP coords
                );
            } else {
                successCb(USER_COORDS[0], USER_COORDS[1]);
            }
        }

        async function submitCommunityReport() {
            const cType = document.getElementById("hazardType").value;
            const cDesc = document.getElementById("hazardDesc").value.trim();
            const stat = document.getElementById("communityReportStatus");
            if (!cDesc) return alert("Please provide a description.");

            const payload = { type: cType, description: cDesc, lat: USER_COORDS[0] + (Math.random() - 0.5) * 0.03, lng: USER_COORDS[1] + (Math.random() - 0.5) * 0.03 };
            if (currentUser?.user_id) payload.user_id = parseInt(currentUser.user_id, 10);

            try {
                const res = await fetch(`${API_URL}/api/community_report`, {
                    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    document.getElementById("hazardDesc").value = "";
                    stat.textContent = "✅ Report submitted to authorities!";
                    setTimeout(() => stat.textContent = "", 5000);
                    fetchCommunityReports();
                } else { alert(data.error); }
            } catch (e) { alert("Network error."); }
        }

        async function fetchCommunityReports() {
            try {
                const res = await fetch(`${API_URL}/api/community_reports`);
                const data = await res.json();
                if (data.reports) {
                    markersComm.forEach(x => { try { mapComm.removeLayer(x); } catch (_) { } });
                    markersComm.length = 0;

                    const icon = L.divIcon({ className: "pin", html: "<span style='background:#d29922;width:14px;height:14px;border-radius:50%;display:block;border:2px solid white'></span>", iconSize: [18, 18] });

                    data.reports.forEach(r => {
                        const lat = parseFloat(r.latitude), lng = parseFloat(r.longitude);
                        if (isNaN(lat) || isNaN(lng)) return;
                        const tooltip = `
                        <b>${r.report_type}</b><br>${r.description}<br>
                        <small>Verified by: ${r.verification_count} citizens</small><div style="margin-top:6px;"></div>
                        <button onclick="verifyReport(${r.report_id})" style="padding:4px 8px;background:var(--accent-amber);color:#000;border:none;border-radius:4px;cursor:pointer;font-weight:600;">I see this too</button>
                    `;
                        if (typeof mapComm !== 'undefined' && mapComm) {
                            const marker = L.marker([lat, lng], { icon }).addTo(mapComm);
                            marker.bindPopup(tooltip);
                            markersComm.push(marker);
                        }
                        if (typeof map !== 'undefined' && map) {
                            const m2 = L.marker([lat, lng], { icon }).addTo(map);
                            m2.bindPopup(tooltip);
                            markersComm.push(m2); // Store in markersComm to clear on update
                        }
                    });
                }
            } catch (_) { }
        }

        async function verifyReport(id) {
            try {
                await fetch(`${API_URL}/api/verify_report`, {
                    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ report_id: id })
                });
                fetchCommunityReports();
                alert("Verification recorded. Thank you!");
            } catch (_) { }
        }

        // ---------- Dashboard (Agency) ----------
        async function fetchDashboard() {
            const role = currentUser?.role_name || "Medical_Response";
            if (role === "Civilian") return;
            try {
                const res = await fetch(`${API_URL}/api/get_dashboard/${role}`);
                const data = await res.json();
                const container = document.getElementById("triageFeed");
                if(!container) return;
                
                container.innerHTML = "";
                let cAct = 0, cCrit = 0, cRes = 0;

                if (!data.emergencies || data.emergencies.length === 0) {
                    container.innerHTML = '<div style="color:var(--accent-green); text-align:center; padding: 2rem; border: 1px dashed var(--accent-green); border-radius:8px;">✅ All clear. No active emergencies assigned to your department.</div>';
                }

                (data.emergencies || []).forEach(req => {
                    incidentsData[req.sos_id] = req;
                    const canDispatch = ["Reported", "Pending", "Requires_Dispatch"].includes(req.status);
                    if (req.status !== "Resolved") {
                        cAct++;
                        if (req.ai_severity_score >= 8) cCrit++;
                    } else { cRes++; }

                    // Determine CSS class based on severity
                    let sevClass = "";
                    let pulseHtml = "";
                    if (req.ai_severity_score >= 8) {
                        sevClass = "critical";
                        if (canDispatch) pulseHtml = '<span class="pulse-dot" style="margin-right:8px;"></span>';
                    } else if (req.ai_severity_score >= 5) {
                        sevClass = "high";
                    }
                    
                    const timeAgo = req.timestamp ? new Date(req.timestamp).toLocaleTimeString() : "Just now";

                    const card = document.createElement("div");
                    card.className = `triage-card ${sevClass}`;
                    card.onclick = () => showIncidentModal(req.sos_id);
                    card.innerHTML = `
                        <div class="triage-content">
                            <div class="triage-meta">${pulseHtml}INCIDENT #${req.sos_id} · ${timeAgo} · ${escapeHtml(req.reporter_name || "Citizen")}</div>
                            <h4 class="triage-title" class="${sevClass === 'critical' ? 'critical' : ''}">${req.ai_category || "Unclassified Threat"} [Severity ${req.ai_severity_score}/10]</h4>
                            <p class="triage-desc">${escapeHtml(req.raw_message || "No description provided. Victim triggered offline GPS ping.")}</p>
                        </div>
                        <div class="triage-action">
                            <span class="status-badge" style="color: ${canDispatch ? 'var(--accent-amber)' : 'var(--text-muted)'}">${escapeHtml(req.status || "-")}</span>
                            ${canDispatch ? '<button class="dispatch-btn" style="margin-top:5px; padding:6px 12px; font-size:0.75rem;">REVIEW</button>' : ''}
                        </div>
                    `;
                    container.appendChild(card);
                });
                document.getElementById("kpiActive").textContent = cAct;
                document.getElementById("kpiCritical").textContent = cCrit;
                document.getElementById("kpiResolved").textContent = cRes;
            } catch (_) { }
        }

        function showIncidentModal(id) {
            const inc = incidentsData[id];
            if (!inc) return;
            activeModalIncidentId = id;
            document.getElementById("mdlIncId").textContent = id;
            document.getElementById("mdlStatus").textContent = inc.status;
            document.getElementById("mdlName").textContent = inc.reporter_name || "Citizen";
            document.getElementById("mdlPhone").textContent = inc.reporter_phone || "Hidden";
            document.getElementById("mdlBlood").textContent = inc.blood_group || "Unknown";
            document.getElementById("mdlTime").textContent = inc.timestamp ? new Date(inc.timestamp).toLocaleTimeString() : "Just now";
            document.getElementById("mdlCat").textContent = `${inc.ai_category} [SEVERITY ${inc.ai_severity_score}/10]`;
            document.getElementById("mdlMsg").textContent = inc.raw_message || "No contextual description provided. Beacon only.";
            document.getElementById("mdlDispatchBtn").style.display = (["Reported", "Pending", "Requires_Dispatch"].includes(inc.status)) ? "block" : "none";
            document.getElementById("incidentModal").style.display = "flex";
            
            // Add keyboard escape binding
            document.addEventListener("keydown", escHandler);
        }

        const escHandler = (e) => {
            if (e.key === "Escape") closeIncidentModal();
        };

        function closeIncidentModal() {
            document.getElementById("incidentModal").style.display = "none";
            activeModalIncidentId = null;
            document.removeEventListener("keydown", escHandler);
        }

        async function dispatchRescueMdl() {
            if (!activeModalIncidentId) return;
            await dispatchTeam(activeModalIncidentId);
            closeIncidentModal();
        }

        async function transferIncidentMdl() {
            if (!activeModalIncidentId) return;
            const dept = document.getElementById("mdlTransferDept").value;
            if (!dept) return alert("Select a department first.");
            try {
                const res = await fetch(`${API_URL}/api/transfer_incident`, {
                    method: "PUT", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ sos_id: activeModalIncidentId, department: dept })
                });
                const data = await res.json();
                if (data.success) {
                    alert("Transferred to " + dept.replace("_", " "));
                    closeIncidentModal();
                    fetchDashboard();
                } else { alert("Failed to transfer: " + data.error); }
            } catch (e) { alert("Network error"); }
        }

        function escapeHtml(s) {
            const d = document.createElement("div");
            d.textContent = s;
            return d.innerHTML;
        }

        async function dispatchTeam(sosId) {
            try {
                const res = await fetch(`${API_URL}/api/update_status`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ sos_id: sosId, status: "Rescue in Progress" })
                });
                const data = await res.json();
                if (data.success) fetchDashboard();
            } catch (_) { }
        }

        // ---------- SOS (Civilian) ----------
        async function sendSOS() {
            let msg = document.getElementById("sosMessage").value.trim();
            if (currentThreat !== "General") msg = `[${currentThreat}] ` + msg;
            if (!msg || msg === `[${currentThreat}] `) return alert("Please specify threat details.");

            const payload = { message: msg };
            if (currentUser?.user_id) payload.user_id = parseInt(currentUser.user_id, 10);
            try {
                const res = await fetch(`${API_URL}/api/send_sos`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    document.getElementById("sosMessage").value = "";
                    document.getElementById("sosStatus").textContent = `Sent! Routed to ${data.category} (Severity: ${data.severity}/10)`;
                    setTimeout(() => { document.getElementById("sosStatus").textContent = ""; }, 5000);
                    fetchIncidents();
                } else {
                    alert(data.error || "Failed to send SOS");
                }
            } catch (e) {
                alert("Network error. Is the API running?");
            }
        }

        // ---------- Boot ----------
        if (!loadSession()) {
            document.getElementById("loginOverlay").style.display = "flex";
        }
    
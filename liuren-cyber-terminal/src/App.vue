<template>
  <div id="app">
    <!-- 左侧控制面板 -->
    <div class="control-panel">
      <h2 class="panel-title">时空参数阵列</h2>
      
      <div class="form-group">
        <label class="form-label">公历时间 / Solar Time</label>
        <div class="time-input-group">
          <input 
            type="datetime-local" 
            v-model="timeStr"
            class="form-input"
            step="1"
          />
          <button 
            type="button" 
            class="sync-button"
            @click="syncCurrentTime"
            title="同步到当前系统时间"
          >
            ↻ 同步此刻
          </button>
        </div>
      </div>
      
      <div class="form-group">
        <label class="form-label">地理位置 / Location</label>
        <div class="location-input-group">
          <input 
            type="text" 
            v-model="locationInput"
            class="form-input"
            placeholder="输入城市名或经度..."
            @focus="showCityDropdown = true"
            @input="showCityDropdown = true"
            @blur="handleCityBlur"
          />
          <button 
            type="button" 
            class="sync-button"
            @click="networkLocate"
            title="网络IP定位获取物理坐标"
          >
            ⌖ 网络定位
          </button>
          
          <!-- 自定义赛博风格下拉菜单 -->
          <ul v-if="showCityDropdown" class="cyber-dropdown">
            <li 
              v-for="city in filteredCities" 
              :key="`${city.name}-${city.en}`"
              @click="selectCity(city)"
              class="dropdown-item"
            >
              <span class="city-name">{{ city.name }}</span>
              <span class="city-en">{{ city.en }}</span>
              <span class="city-lon">{{ city.lon }}°E</span>
            </li>
            <li v-if="filteredCities.length === 0" class="dropdown-item empty">
              未找到匹配的城市
            </li>
          </ul>
        </div>
      </div>
      
      <div class="form-group">
        <label class="form-label">性别 / Gender</label>
        <select v-model="gender" class="form-input form-select">
          <option value="男">男 (Male)</option>
          <option value="女">女 (Female)</option>
        </select>
      </div>
      
      <div class="form-group">
        <label class="form-label">出生年份 / Birth Year</label>
        <select v-model="birthYear" class="form-input form-select">
          <option 
            v-for="year in yearOptions" 
            :key="year" 
            :value="year"
          >
            {{ year }} 年
          </option>
        </select>
      </div>
      
      <div class="form-group">
        <label class="form-label">占测事由 / Intent</label>
        <textarea 
          v-model="eventIntent"
          class="form-input form-textarea"
          placeholder="请输入您要占测的具体事由..."
        ></textarea>
      </div>
      
      <button 
        class="initiate-button" 
        @click="spacetimeDeduce"
        :disabled="isLoading"
      >
        <span v-if="isLoading" class="loading"></span>
        <span v-else>启动推演 (INITIATE)</span>
      </button>
    </div>
    
    <!-- 中央全息天体星盘 -->
    <div class="astrolabe-container">
      <div class="astrolabe">
        <!-- 天体轨道 -->
        <div class="celestial-orbit orbit-outer"></div>
        <div class="celestial-orbit orbit-inner"></div>
        
        <!-- 核心发光体 -->
        <div class="core"></div>
        
        <!-- 地盘宫位标记 -->
        <div 
          v-for="(branch, index) in branches" 
          :key="`earth-${index}`"
          class="branch-marker"
          :style="getEarthBranchStyle(index)"
        >
          {{ branch }}
        </div>
        
        <!-- 天盘旋转层 -->
        <div class="inner-astrolabe" :style="{ transform: innerRotation }">
          <!-- 天盘宫位标记 -->
          <div 
            v-for="(branch, index) in branches" 
            :key="`sky-${index}`"
            class="branch-marker"
            :style="getSkyBranchStyle(index)"
          >
            {{ branch }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- 底部结果展示面板 -->
    <div v-if="result" class="result-panel">
      <div class="result-grid">
        <div class="result-item">
          <div class="result-label">四柱八字</div>
          <div class="result-value">
            {{ result.spacetime_params.four_pillars.year }} 
            {{ result.spacetime_params.four_pillars.month }}
            {{ result.spacetime_params.four_pillars.day }}
            {{ result.spacetime_params.four_pillars.hour }}
          </div>
        </div>
        
        <div class="result-item">
          <div class="result-label">真太阳时</div>
          <div class="result-value">{{ result.spacetime_params.true_solar_time }}</div>
        </div>
        
        <div class="result-item">
          <div class="result-label">占测事由</div>
          <div class="result-value">{{ result.event_intent }}</div>
        </div>
        
        <div class="result-item">
          <div class="result-label">地理位置</div>
          <div class="result-value">{{ resolvedLocationName }} ({{ currentLongitude }}°E)</div>
        </div>
        
        <div class="result-item">
          <div class="result-label">本命行年</div>
          <div class="result-value">
            {{ result.spacetime_params.ben_ming }} / 
            {{ result.spacetime_params.xing_nian }}
          </div>
        </div>
        
        <div class="result-item">
          <div class="result-label">昼夜判定</div>
          <div class="result-value">{{ result.spacetime_params.is_daytime }}</div>
        </div>
        
        <div class="result-item">
          <div class="result-label">天盘偏移</div>
          <div class="result-value">{{ offset }} 宫位 ({{ branches[offset] }}宫)</div>
        </div>
      </div>
      
      <div v-if="result.route_warning" class="route-warning">
        {{ result.route_warning }}
      </div>
      
      <!-- 大六壬解码区 -->
      <div v-if="oracleReading" class="oracle-panel" :class="{ 'error-panel': isError }">
        <div class="oracle-header">
          <span class="oracle-title">
            {{ isError ? '系统警报 (System Alert)' : '大六壬解码区 (Oracle Decryption)' }}
          </span>
          <span v-if="isTyping" class="typing-indicator">
            {{ isError ? '诊断中...' : '解码中...' }}
          </span>
        </div>
        <div class="oracle-content">
          <div class="oracle-text" :class="{ 'error-text': isError }">{{ displayedOracle }}</div>
          <span v-if="isTyping" class="cursor">|</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from "vue";
import { Command } from '@tauri-apps/plugin-shell';
// 启动 Python 伴生引擎
const startEngine = async () => {
  try {
    const command = Command.sidecar('liuren-engine');
    const child = await command.spawn();
    console.log('✅ 底层物理引擎已成功点火, PID:', child.pid);
  } catch (error) {
    console.error('❌ 物理引擎启动失败:', error);
  }
};

// 在页面加载时启动引擎
startEngine();

// 地支十二宫位
const branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];

// 定义城市数据类型，满足 TypeScript 的严格检查
interface CityNode {
  name: string;
  en: string;
  lon: number;
}

// 全球城市微型数据库（严格类型响应式数组）
const CITY_DATABASE = ref<CityNode[]>([
  // ==== 中国核心城市 & 省会 (精确至小数点后两位) ====
  { name: '北京', en: 'Beijing', lon: 116.40 },
  { name: '上海', en: 'Shanghai', lon: 121.47 },
  { name: '天津', en: 'Tianjin', lon: 117.20 },
  { name: '重庆', en: 'Chongqing', lon: 106.50 },
  { name: '哈尔滨', en: 'Harbin', lon: 126.63 },
  { name: '长春', en: 'Changchun', lon: 125.35 },
  { name: '沈阳', en: 'Shenyang', lon: 123.38 },
  { name: '大连', en: 'Dalian', lon: 121.62 },
  { name: '呼和浩特', en: 'Hohhot', lon: 111.65 },
  { name: '石家庄', en: 'Shijiazhuang', lon: 114.48 },
  { name: '太原', en: 'Taiyuan', lon: 112.53 },
  { name: '济南', en: 'Jinan', lon: 117.00 },
  { name: '青岛', en: 'Qingdao', lon: 120.33 },
  { name: '郑州', en: 'Zhengzhou', lon: 113.62 },
  { name: '西安', en: 'Xi\'an', lon: 108.94 },
  { name: '兰州', en: 'Lanzhou', lon: 103.82 },
  { name: '银川', en: 'Yinchuan', lon: 106.27 },
  { name: '西宁', en: 'Xining', lon: 101.74 },
  { name: '乌鲁木齐', en: 'Urumqi', lon: 87.68 },
  { name: '拉萨', en: 'Lhasa', lon: 91.11 },
  { name: '成都', en: 'Chengdu', lon: 104.06 },
  { name: '贵阳', en: 'Guiyang', lon: 106.71 },
  { name: '昆明', en: 'Kunming', lon: 102.73 },
  { name: '武汉', en: 'Wuhan', lon: 114.30 },
  { name: '长沙', en: 'Changsha', lon: 112.93 },
  { name: '南昌', en: 'Nanchang', lon: 115.89 },
  { name: '合肥', en: 'Hefei', lon: 117.27 },
  { name: '南京', en: 'Nanjing', lon: 118.79 },
  { name: '苏州', en: 'Suzhou', lon: 120.58 },
  { name: '杭州', en: 'Hangzhou', lon: 120.15 },
  { name: '福州', en: 'Fuzhou', lon: 119.30 },
  { name: '厦门', en: 'Xiamen', lon: 118.08 },
  { name: '广州', en: 'Guangzhou', lon: 113.26 },
  { name: '深圳', en: 'Shenzhen', lon: 114.05 },
  { name: '南宁', en: 'Nanning', lon: 108.32 },
  { name: '海口', en: 'Haikou', lon: 110.35 },
  { name: '台北', en: 'Taipei', lon: 121.56 },
  { name: '香港', en: 'Hong Kong', lon: 114.16 },
  { name: '澳门', en: 'Macau', lon: 113.54 },

  // ==== 国际枢纽 & 标志性城市 ====
  { name: '东京', en: 'Tokyo', lon: 139.69 },
  { name: '大阪', en: 'Osaka', lon: 135.50 },
  { name: '首尔', en: 'Seoul', lon: 126.97 },
  { name: '新加坡', en: 'Singapore', lon: 103.81 },
  { name: '曼谷', en: 'Bangkok', lon: 100.50 },
  { name: '迪拜', en: 'Dubai', lon: 55.27 },
  { name: '孟买', en: 'Mumbai', lon: 72.87 },
  { name: '莫斯科', en: 'Moscow', lon: 37.61 },
  { name: '伦敦', en: 'London', lon: -0.12 },
  { name: '巴黎', en: 'Paris', lon: 2.35 },
  { name: '柏林', en: 'Berlin', lon: 13.40 },
  { name: '罗马', en: 'Rome', lon: 12.49 },
  { name: '纽约', en: 'New York', lon: -74.00 },
  { name: '洛杉矶', en: 'Los Angeles', lon: -118.24 },
  { name: '芝加哥', en: 'Chicago', lon: -87.62 },
  { name: '旧金山', en: 'San Francisco', lon: -122.41 },
  { name: '多伦多', en: 'Toronto', lon: -79.38 },
  { name: '温哥华', en: 'Vancouver', lon: -123.12 },
  { name: '悉尼', en: 'Sydney', lon: 151.20 },
  { name: '墨尔本', en: 'Melbourne', lon: 144.96 },
  { name: '圣保罗', en: 'Sao Paulo', lon: -46.63 },
  { name: '布宜诺斯艾利斯', en: 'Buenos Aires', lon: -58.38 },
  { name: '开普敦', en: 'Cape Town', lon: 18.42 }
]);
// 天盘偏移量
const offset = ref(0);

// 计算内圈旋转角度（使用高级物理动画曲线）
const innerRotation = computed(() => `rotate(${offset.value * 30}deg)`);

// 后端API地址
const API_BASE_URL = 'http://127.0.0.1:8000';

// 年份选项（1920-2026）
const yearOptions = Array.from({ length: 107 }, (_, i) => 1920 + i);

// 时空推演表单数据
const timeStr = ref('');
const locationInput = ref('北京');
const gender = ref('男');
const birthYear = ref(1990);
const eventIntent = ref('');

// 智能解析计算属性
const currentLongitude = computed(() => {
  const input = locationInput.value.trim();
  
  // 优先正则提取：杭州 (120.2°E) 格式
  const match = input.match(/\(([-+]?[\d.]+)°/);
  if (match && match[1]) {
    return parseFloat(match[1]);
  }
  
  // 其次纯数字提取：120.2 格式
  if (/^-?\d+(\.\d+)?$/.test(input)) {
    return parseFloat(input);
  }
  
  // 最后模糊匹配城市名称（中英文，忽略大小写）
  const matchedCity = CITY_DATABASE.value.find(city => 
    city.name.toLowerCase().includes(input.toLowerCase()) ||
    city.en.toLowerCase().includes(input.toLowerCase())
  );
  
  return matchedCity ? matchedCity.lon : 116.4; // 默认北京经度
});

const resolvedLocationName = computed(() => {
  const input = locationInput.value.trim();
  
  // 优先正则提取：杭州 (120.2°E) 格式
  const match = input.match(/(.+?)\s*\([-+]?[\d.]+°/);
  if (match && match[1]) {
    return match[1].trim();
  }
  
  // 如果是纯数字，返回手动坐标
  if (/^-?\d+(\.\d+)?$/.test(input)) {
    return '手动坐标 (Manual)';
  }
  
  // 在数据库中模糊匹配城市名称
  const matchedCity = CITY_DATABASE.value.find(city => 
    city.name.toLowerCase().includes(input.toLowerCase()) ||
    city.en.toLowerCase().includes(input.toLowerCase())
  );
  
  return matchedCity ? `${matchedCity.name} / ${matchedCity.en}` : '未知区域 (默认北京)';
});

// 自定义自动补全组件状态
const showCityDropdown = ref(false);

// 处理城市输入框失去焦点的延时逻辑
const handleCityBlur = () => {
  setTimeout(() => {
    showCityDropdown.value = false;
  }, 200);
};

// 过滤城市列表
const filteredCities = computed(() => {
  // 剥离类似 " (120.2°E)" 的部分，提取纯城市名
  const rawInput = locationInput.value.replace(/\s*\(.*?\)/, '').trim().toLowerCase();
  
  if (!rawInput) {
    // 输入为空时返回前6条
    return CITY_DATABASE.value.slice(0, 6);
  }
  
  // 根据纯城市名过滤（支持中英文）
  const filtered = CITY_DATABASE.value.filter(city => 
    city.name.toLowerCase().includes(rawInput) ||
    city.en.toLowerCase().includes(rawInput)
  );
  
  // 最多返回6条结果
  return filtered.slice(0, 6);
});

// 选择城市
const selectCity = (city: any) => {
  locationInput.value = `${city.name} (${city.lon}°E)`;
  showCityDropdown.value = false;
};

// 状态管理
const isLoading = ref(false);
const result = ref<any>(null);
const oracleReading = ref('');
const isTyping = ref(false);
const displayedOracle = ref('');
const isError = ref(false);

// 初始化默认时间（当前时间）
const initDefaultTime = () => {
  syncCurrentTime();
};

// 同步当前系统时间
const syncCurrentTime = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  
  timeStr.value = `${year}-${month}-${day}T${hours}:${minutes}`;
};

// 网络IP定位功能
const networkLocate = async () => {
  oracleReading.value = '[SYS_INFO] 正在扫描网络节点，请求物理坐标...';
  await typeOracleText(oracleReading.value, false);
  
  try {
    const response = await fetch('https://ipapi.co/json/', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.longitude) {
      const cityName = data.city || 'Network Location';
      const lonVal = parseFloat(data.longitude);
      const countryName = data.country_name || '未知国家';
      
      // 检查数据库中是否已存在该城市
      const existingCity = CITY_DATABASE.value.find(city => 
        city.name === cityName || city.en === cityName
      );
      
      // 如果不存在，动态注入到数据库开头
      if (!existingCity) {
        CITY_DATABASE.value.unshift({
          name: cityName,
          en: cityName,
          lon: lonVal
        });
      }
      
      // 显示标准格式：城市名 (经度°E)
      locationInput.value = `${cityName} (${lonVal}°E)`;
      
      // 强制关闭下拉菜单
      showCityDropdown.value = false;
      
      oracleReading.value = `[SYS_SUCCESS] 节点锁定: ${cityName}, ${countryName}。经度: ${lonVal.toFixed(2)}°`;
      await typeOracleText(oracleReading.value, false);
    } else {
      throw new Error('API返回数据格式异常');
    }
    
  } catch (error: any) {
    console.error('网络定位错误:', error);
    
    let errorMessage = '[SYS_ERR] 网络定位超时或被拦截，请手动输入城市';
    
    if (error.message.includes('HTTP错误')) {
      errorMessage = `[SYS_ERR] 网络定位服务异常: ${error.message}`;
    } else if (error.message.includes('Failed to fetch')) {
      errorMessage = '[SYS_ERR] 网络连接失败，请检查网络设置';
    }
    
    oracleReading.value = errorMessage;
    await typeOracleText(oracleReading.value, true);
  }
};

// 大六壬打字机效果
const typeOracleText = async (text: string, error: boolean = false) => {
  isTyping.value = true;
  isError.value = error;
  displayedOracle.value = '';
  
  for (let i = 0; i < text.length; i++) {
    displayedOracle.value += text[i];
    await new Promise(resolve => setTimeout(resolve, 30)); // 30ms延迟，模拟打字效果
  }
  
  isTyping.value = false;
};

// 设置偏移量
function setOffset(value: number) {
  offset.value = value % 12;
}

// 重置旋转
function resetRotation() {
  setOffset(0);
  result.value = null;
  oracleReading.value = '';
  isError.value = false;
}

// 计算地盘宫位位置
function getEarthBranchStyle(index: number) {
  const angle = (index * 30) * Math.PI / 180;
  const radius = 200;
  const x = radius * Math.sin(angle);
  const y = -radius * Math.cos(angle);
  
  return {
    left: `calc(50% + ${x}px)`,
    top: `calc(50% + ${y}px)`,
    transform: 'translate(-50%, -50%)'
  };
}

// 计算天盘宫位位置
function getSkyBranchStyle(index: number) {
  const angle = (index * 30) * Math.PI / 180;
  const radius = 160;
  const x = radius * Math.sin(angle);
  const y = -radius * Math.cos(angle);
  
  return {
    left: `calc(50% + ${x}px)`,
    top: `calc(50% + ${y}px)`,
    transform: 'translate(-50%, -50%)'
  };
}

// 时空推演 - SSE流式调用后端API进行真太阳时推演
async function spacetimeDeduce() {
  if (!timeStr.value || !eventIntent.value) {
    oracleReading.value = '[VALIDATION_ERR] 时空参数不完整：请填写时间和占测事由';
    await typeOracleText(oracleReading.value, true);
    return;
  }
  
  isLoading.value = true;
  isError.value = false;
  oracleReading.value = '';
  displayedOracle.value = '';
  
  try {
    const formattedTime = timeStr.value.replace('T', ' ') + ':00';
    
    // 1. 发起 SSE 流式 POST 请求
    const response = await fetch(`${API_BASE_URL}/api/deduce/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        time_str: formattedTime,
        longitude: currentLongitude.value,
        gender: gender.value,
        birth_year: birthYear.value,
        event_intent: eventIntent.value
      })
    });
    
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(errText || `HTTP错误! 状态码: ${response.status}`);
    }
    
    // 2. 获取流式读取器
    const reader = response.body!.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    
    // 3. 循环读取 SSE 数据块
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      
      // 按 \n\n 分割完整的 SSE 事件
      const events = buffer.split('\n\n');
      buffer = events.pop() || ''; // 保留最后一个不完整事件
      
      for (const event of events) {
        const trimmedEvent = event.trim();
        if (!trimmedEvent) continue;
        
        // 提取所有 data: 行（支持多行 data）
        const dataLines = trimmedEvent
          .split('\n')
          .filter(line => line.trimStart().startsWith('data:'))
          .map(line => {
            const idx = line.indexOf('data:');
            return line.slice(idx + 5).trimStart();
          });
        
        if (dataLines.length === 0) continue;
        
        const data = dataLines.join('\n');
        
        // === 终止信号 ===
        if (data === '[DONE]') {
          continue;
        }
        
        // === 错误事件 ===
        if (data.startsWith('[ERROR]') || data.startsWith('[ERR]')) {
          isError.value = true;
          const errMsg = data.replace(/^\[(ERROR|ERR)\]\s*/, '');
          displayedOracle.value += errMsg;
          oracleReading.value += errMsg;
          continue;
        }
        
        // === 尝试解析快照 JSON ===
        let isSnapshot = false;
        try {
          const json = JSON.parse(data);
          
          if (json.type === 'snapshot' || (json.snapshot && json.spacetime_params)) {
            isSnapshot = true;
            
            // 提取引擎快照
            const engineSnapshot = json.snapshot?.snapshot || json.snapshot;
            
            // 计算天盘偏移量（根据初传课序的地盘索引）
            if (engineSnapshot) {
              const routeDecision = engineSnapshot.route_decision;
              const initLessonId = routeDecision?.init_node_lesson_id;
              const fourLessons = engineSnapshot.four_lessons;
              
              if (initLessonId && fourLessons) {
                const initLesson = fourLessons.find((lesson: any) => lesson.id === initLessonId);
                if (initLesson) {
                  setOffset(initLesson.bottom);
                }
              }
            }
            
            // 组装结果对象供星盘渲染
            result.value = {
              spacetime_params: json.spacetime_params || {},
              event_intent: json.event_intent || '',
              route_warning: json.route_warning || ''
            };
          }
        } catch {
          // 非 JSON，作为神谕文本处理
        }
        
        if (isSnapshot) continue;
        
        // === 神谕文本块：逐字追加到终端显示区 ===
        isTyping.value = true;
        displayedOracle.value += data;
        oracleReading.value += data;
        
        // 自动滚动到底部，保持打字机效果在可视区域
        await nextTick();
        const oracleContent = document.querySelector('.oracle-content');
        if (oracleContent) {
          oracleContent.scrollTop = oracleContent.scrollHeight;
        }
      }
    }
    
    // 4. 流结束，收尾
    isTyping.value = false;
    
  } catch (error: any) {
    console.error('推演错误:', error);
    isTyping.value = false;
    
    // 优雅降级：网络错误处理
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      oracleReading.value = '[SYS_ERR] 神经链路断开：无法连接到大六壬底层引擎，请检查后端进程是否存活。';
    } else if (error.message.includes('HTTP错误')) {
      oracleReading.value = `[HTTP_ERR] 服务器响应异常: ${error.message}`;
    } else {
      oracleReading.value = `[ENGINE_ERR] ${error.message}`;
    }
    
    displayedOracle.value = oracleReading.value;
    isError.value = true;
    
    // 如果后端连接失败，回退到前端随机旋转
    const randomOffset = Math.floor(Math.random() * 12);
    setOffset(randomOffset);
    
    result.value = {
      spacetime_params: {
        four_pillars: { year: '--', month: '--', day: '--', hour: '--' },
        true_solar_time: '--',
        ben_ming: '--',
        xing_nian: '--',
        is_daytime: '--'
      },
      event_intent: eventIntent.value,
      route_warning: '[FALLBACK] 后端连接失败，启用本地推演模式'
    };
  } finally {
    isLoading.value = false;
  }
}

// 初始化默认时间
onMounted(() => {
  initDefaultTime();
  
  // 添加星光粒子效果
  const container = document.querySelector('.astrolabe-container');
  if (container) {
    for (let i = 0; i < 50; i++) {
      const star = document.createElement('div');
      star.className = 'star-particle';
      star.style.left = Math.random() * 100 + '%';
      star.style.top = Math.random() * 100 + '%';
      star.style.animationDelay = Math.random() * 3 + 's';
      container.appendChild(star);
    }
  }
});
</script>

<style scoped>
/* 大六壬全息天体运行界面 - 极简科技风格 */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  background: radial-gradient(circle at center, #1a1a24 0%, #09090b 100%);
  color: #f0f0f0;
  min-height: 100vh;
  overflow-x: hidden;
}

#app {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 400px 1fr;
  grid-template-rows: 1fr auto;
  gap: 24px;
  padding: 24px;
}

/* 左侧控制面板 */
.control-panel {
  grid-column: 1;
  grid-row: 1;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 24px;
  letter-spacing: 0.5px;
}

/* 表单样式 */
.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 12px;
  color: #a0a0a0;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.form-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 16px;
  color: #ffffff;
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  outline: none;
}

.form-input:focus {
  border-color: rgba(0, 200, 255, 0.3);
  box-shadow: 0 0 0 2px rgba(0, 200, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
}

.form-input::placeholder {
  color: #666;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
}

.form-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23a0a0a0' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
  background-size: 12px;
}

/* 时间输入组样式 */
.time-input-group {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

.time-input-group .form-input {
  flex: 1;
  margin-bottom: 0;
}

.sync-button {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 0 12px;
  color: #a0a0a0;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}

.sync-button:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(0, 200, 255, 0.3);
  color: #00c6ff;
}

.sync-button:active {
  transform: scale(0.98);
}

/* 位置输入组样式 */
.location-input-group {
  display: flex;
  gap: 8px;
  align-items: stretch;
  position: relative;
}

.location-input-group .form-input {
  flex: 1;
  margin-bottom: 0;
}

/* 赛博风格下拉菜单 */
.cyber-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgba(20, 20, 30, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 200, 255, 0.3);
  border-radius: 8px;
  margin-top: 4px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  z-index: 100;
  max-height: 200px;
  overflow-y: auto;
  list-style: none;
  padding: 4px 0;
}

.dropdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #e0f7ff;
  font-size: 13px;
}

.dropdown-item:hover {
  background: rgba(0, 200, 255, 0.1);
  color: #00c6ff;
  text-shadow: 0 0 8px rgba(0, 200, 255, 0.5);
}

.dropdown-item.empty {
  justify-content: center;
  color: #a0a0a0;
  cursor: default;
}

.dropdown-item.empty:hover {
  background: transparent;
  color: #a0a0a0;
  text-shadow: none;
}

.city-name {
  font-weight: 600;
  flex: 1;
}

.city-en {
  color: #a0a0a0;
  font-size: 11px;
  margin: 0 8px;
}

.city-lon {
  color: #00c6ff;
  font-family: 'Courier New', monospace;
  font-size: 11px;
}

/* 下拉列表选项样式 - 深色主题 */
option {
  background-color: #1a1a24 !important;
  color: #f0f0f0 !important;
  border: none !important;
  outline: none !important;
}

option:hover {
  background-color: #2a2a34 !important;
  color: #ffffff !important;
}

option:checked {
  background-color: #00c6ff !important;
  color: #000000 !important;
}

/* 下拉列表容器样式 */
select option {
  background-color: #1a1a24;
  color: #f0f0f0;
}

select:focus option:checked {
  background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
  color: #000000;
}

/* 按钮样式 */
.initiate-button {
  width: 100%;
  background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
  border: none;
  border-radius: 8px;
  padding: 14px 24px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  text-transform: uppercase;
  letter-spacing: 1px;
  position: relative;
  overflow: hidden;
}

.initiate-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 25px rgba(0, 114, 255, 0.3);
}

.initiate-button:active {
  transform: translateY(0);
}

.initiate-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.initiate-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.initiate-button:hover:not(:disabled)::before {
  left: 100%;
}

/* 星盘容器 */
.astrolabe-container {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

/* 全息天体星盘 */
.astrolabe {
  position: relative;
  width: 500px;
  height: 500px;
}

/* 天体轨道 */
.celestial-orbit {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 
    inset 0 0 20px rgba(255, 255, 255, 0.05),
    0 0 40px rgba(0, 200, 255, 0.1),
    /* 多层极细同心圆阴影 */
    0 0 0 1px rgba(255, 255, 255, 0.02),
    0 0 0 2px rgba(255, 255, 255, 0.01),
    0 0 0 3px rgba(255, 255, 255, 0.005);
}

.orbit-outer {
  width: 100%;
  height: 100%;
  border-color: rgba(255, 255, 255, 0.15);
}

.orbit-inner {
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  border-color: rgba(255, 255, 255, 0.1);
}

/* 核心发光体 */
.core {
  position: absolute;
  width: 60px;
  height: 60px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, #00c6ff 0%, #0072ff 40%, transparent 70%);
  border-radius: 50%;
  box-shadow: 
    0 0 80px rgba(0, 198, 255, 0.8),
    0 0 160px rgba(0, 114, 255, 0.4),
    0 0 240px rgba(0, 72, 255, 0.2);
  animation: pulse 3s ease-in-out infinite;
  z-index: 10;
}

/* 伪元素核心发光体 */
.astrolabe::after {
  content: '';
  position: absolute;
  width: 120px;
  height: 120px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(0, 198, 255, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  box-shadow: 
    inset 0 0 40px rgba(0, 198, 255, 0.2),
    0 0 100px rgba(0, 198, 255, 0.3);
  z-index: 5;
}

/* 天文仪刻度线 */
.astrolabe::before {
  content: '';
  position: absolute;
  width: 95%;
  height: 95%;
  top: 2.5%;
  left: 2.5%;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: 
    radial-gradient(circle at center, transparent 0%, rgba(255, 255, 255, 0.02) 100%),
    repeating-conic-gradient(
      from 0deg,
      rgba(255, 255, 255, 0) 0deg,
      rgba(255, 255, 255, 0.1) 0.5deg,
      rgba(255, 255, 255, 0) 1deg,
      rgba(255, 255, 255, 0) 30deg
    );
}

/* 宫位标记 */
.branch-marker {
  position: absolute;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #ffffff;
  transform-origin: center;
  transition: all 0.3s ease;
}

.branch-marker:hover {
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.2);
}

/* 天盘旋转动画 */
.inner-astrolabe {
  position: absolute;
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  border-radius: 50%;
  transition: transform 4s cubic-bezier(0.2, 0.8, 0.2, 1);
}

/* 结果展示面板 */
.result-panel {
  grid-column: 1 / -1;
  grid-row: 2;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 24px;
  margin-top: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.result-item {
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border-left: 3px solid rgba(0, 200, 255, 0.5);
}

.result-label {
  font-size: 12px;
  color: #a0a0a0;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.result-value {
  font-size: 16px;
  color: #ffffff;
  font-weight: 500;
}

.route-warning {
  grid-column: 1 / -1;
  padding: 12px 16px;
  background: rgba(100, 200, 100, 0.05);
  border-radius: 6px;
  border-left: 3px solid rgba(100, 200, 100, 0.3);
  font-size: 13px;
  line-height: 1.5;
  color: #a0d0a0;
  font-family: 'Courier New', monospace;
  font-weight: 400;
}

.route-warning::before {
  content: '[INFO] ';
  color: #80c080;
  font-weight: 600;
}

/* 加载状态 */
.loading {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #00c6ff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 大六壬解码区 */
.oracle-panel {
  grid-column: 1 / -1;
  backdrop-filter: blur(20px);
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 200, 255, 0.3);
  border-radius: 16px;
  padding: 24px;
  margin-top: 24px;
  box-shadow: 0 0 40px rgba(0, 200, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.oracle-panel.error-panel {
  border-color: rgba(255, 0, 100, 0.5);
  box-shadow: 0 0 40px rgba(255, 0, 100, 0.2);
  background: rgba(255, 0, 0, 0.1);
}

.oracle-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 200, 255, 0.1), transparent);
  animation: scanline 3s linear infinite;
}

.oracle-panel.error-panel::before {
  background: linear-gradient(90deg, transparent, rgba(255, 0, 100, 0.2), transparent);
}

@keyframes scanline {
  0% { left: -100%; }
  100% { left: 100%; }
}

.oracle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 200, 255, 0.2);
}

.oracle-panel.error-panel .oracle-header {
  border-bottom-color: rgba(255, 0, 100, 0.3);
}

.oracle-title {
  font-size: 16px;
  font-weight: 600;
  color: #00c6ff;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.oracle-panel.error-panel .oracle-title {
  color: #ff0064;
}

.typing-indicator {
  font-size: 12px;
  color: #a0a0a0;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.oracle-content {
  position: relative;
  min-height: 80px;
}

.oracle-text {
  font-size: 14px;
  line-height: 1.6;
  color: #e0f7ff;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.oracle-text.error-text {
  background: linear-gradient(135deg, #ff0064 0%, #ff2d95 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background: #00c6ff;
  margin-left: 2px;
  animation: blink 1s infinite;
  vertical-align: middle;
}

.oracle-panel.error-panel .cursor {
  background: #ff0064;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 星光粒子效果 */
.star-particle {
  position: absolute;
  width: 1px;
  height: 1px;
  background: #ffffff;
  border-radius: 50%;
  animation: twinkle 3s infinite;
  opacity: 0;
}

@keyframes twinkle {
  0%, 100% { opacity: 0; transform: scale(0.5); }
  50% { opacity: 1; transform: scale(1); }
}

/* 响应式设计 */
@media (max-width: 1024px) {
  #app {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
    gap: 16px;
    padding: 16px;
  }
  
  .control-panel {
    grid-column: 1;
    grid-row: 1;
  }
  
  .astrolabe-container {
    grid-column: 1;
    grid-row: 2;
    min-height: 300px;
  }
  
  .astrolabe {
    width: 300px;
    height: 300px;
  }
  
  .result-panel {
    grid-column: 1;
    grid-row: 3;
  }
}

@media (max-width: 768px) {
  .astrolabe {
    width: 250px;
    height: 250px;
  }
  
  .branch-marker {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }
  
  .result-grid {
    grid-template-columns: 1fr;
  }
  
  .oracle-panel {
    padding: 16px;
    margin-top: 16px;
  }
  
  .oracle-title {
    font-size: 14px;
  }
  
  .oracle-text {
    font-size: 13px;
  }
}
</style>
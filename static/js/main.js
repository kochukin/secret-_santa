// Crear efecto de nieve
function createSnowflakes() {
    const snowflakesContainer = document.getElementById('snowfall');
    const numberOfSnowflakes = 50;

    for (let i = 0; i < numberOfSnowflakes; i++) {
        const snowflake = document.createElement('div');
        snowflake.className = 'snowflake';
        snowflake.innerHTML = '❄';
        snowflake.style.left = `${Math.random() * 100}vw`;
        snowflake.style.animationDuration = `${Math.random() * 3 + 2}s`;
        snowflake.style.opacity = Math.random();
        snowflake.style.fontSize = `${Math.random() * 10 + 10}px`;
        snowflakesContainer.appendChild(snowflake);
    }
}

// Cambiar entre tabs
function showTab(tabName) {
    const registerForm = document.getElementById('registerForm');
    const groupForm = document.getElementById('groupForm');
    const drawForm = document.getElementById('drawForm');
    const tabs = document.querySelectorAll('.tab');

    if (tabName === 'register') {
        registerForm.style.display = 'block';
        groupForm.style.display = 'none';
        drawForm.style.display = 'none';
        tabs[0].classList.add('active');
        tabs[1].classList.remove('active');
        tabs[2].classList.remove('active');
    } else if (tabName === 'group') {
        registerForm.style.display = 'none';
        groupForm.style.display = 'block';
        drawForm.style.display = 'none';
        tabs[0].classList.remove('active');
        tabs[1].classList.add('active');
        tabs[2].classList.remove('active');
    } else {
        registerForm.style.display = 'none';
        groupForm.style.display = 'none';
        drawForm.style.display = 'block';
        tabs[0].classList.remove('active');
        tabs[1].classList.remove('active');
        tabs[2].classList.add('active');
    }
}

// Mostrar toast notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type} animate__animated animate__fadeInRight`;
    
    const icon = type === 'success' ? '✅' : '❌';
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('animate__fadeInRight');
        toast.classList.add('animate__fadeOutRight');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// Loading spinner
function showLoading() {
    const loading = document.createElement('div');
    loading.className = 'loading';
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.querySelector('.loading');
    if (loading) {
        loading.remove();
    }
}

// Efectos de confeti
function showConfetti() {
    const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff'];
    const confettiCount = 100;
    
    for (let i = 0; i < confettiCount; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.left = `${Math.random() * 100}vw`;
        confetti.style.animationDuration = `${Math.random() * 3 + 2}s`;
        confetti.style.opacity = Math.random();
        document.body.appendChild(confetti);
        
        setTimeout(() => confetti.remove(), 5000);
    }
}

// Manejar envío de formulario de registro
async function handleSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    showLoading();

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData)),
        });

        const data = await response.json();
        
        if (response.ok) {
            showToast('¡Registro exitoso! 🎉', 'success');
            showConfetti();
            form.reset();
        } else {
            showToast(data.error || 'Error en el registro', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
    } finally {
        hideLoading();
    }
}

// Manejar creación de grupo
async function handleGroupSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    showLoading();

    try {
        const response = await fetch('/api/groups', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData)),
        });

        const data = await response.json();
        
        if (response.ok) {
            showToast(`¡Grupo creado exitosamente! 🎉\nCódigo: ${data.data.groupCode}`, 'success');
            showConfetti();
            form.reset();
            document.getElementById('drawForm').style.display = 'block';
            document.getElementById('groupCodeForAssign').value = data.data.groupCode;
            loadGroupSummary(data.data.groupCode);
        } else {
            showToast(data.error || 'Error al crear el grupo', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
    } finally {
        hideLoading();
    }
}

// Cargar resumen del grupo
async function loadGroupSummary(groupCode) {
    try {
        const response = await fetch(`/api/groups/${groupCode}/participants`);
        const data = await response.json();
        
        if (response.ok) {
            const summary = document.getElementById('groupInfo');
            summary.innerHTML = `
                <div class="group-info">
                    <p><strong>Nombre:</strong> ${data.group.groupName}</p>
                    <p><strong>Código:</strong> ${data.group.code}</p>
                    <p><strong>Presupuesto:</strong> $${data.group.budget}</p>
                    <p><strong>Participantes:</strong> ${data.group.participants.length}/${data.group.maxParticipants}</p>
                    <p><strong>Fecha:</strong> ${data.group.exchangeDate}</p>
                </div>
                <div class="participants-list">
                    <h4>Participantes:</h4>
                    <ul>
                        ${data.group.participants.map(p => `
                            <li>${p.name} (${p.email})</li>
                        `).join('')}
                    </ul>
                </div>
            `;
            document.getElementById('groupSummary').style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading group summary:', error);
    }
}

// Realizar sorteo
async function handleAssignment() {
    const groupCode = document.getElementById('groupCodeForAssign').value;
    
    if (!groupCode) {
        showToast('Por favor, introduce el código del grupo', 'error');
        return;
    }

    showLoading();
    
    try {
        const response = await fetch(`/api/groups/${groupCode}/assign`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showConfetti();
            showToast('¡Sorteo realizado exitosamente! 🎁\nLos participantes recibirán un email con su asignación.', 'success');
            loadGroupSummary(groupCode);
        } else {
            showToast(data.error || 'Error en el sorteo', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
    } finally {
        hideLoading();
    }
}

// Validar formularios
function validateForm(formData) {
    const errors = [];
    
    // Validar nombre
    const name = formData.get('name');
    if (name && name.length < 2) {
        errors.push('El nombre debe tener al menos 2 caracteres');
    }
    
    // Validar email
    const email = formData.get('email');
    if (email && !email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        errors.push('El email no es válido');
    }
    
    // Validar fecha de intercambio
    const exchangeDate = formData.get('exchangeDate');
    if (exchangeDate) {
        const selectedDate = new Date(exchangeDate);
        const today = new Date();
        if (selectedDate < today) {
            errors.push('La fecha de intercambio debe ser futura');
        }
    }
    
    // Validar presupuesto
    const budget = formData.get('budget');
    if (budget && (isNaN(budget) || budget <= 0)) {
        errors.push('El presupuesto debe ser un número positivo');
    }
    
    return errors;
}

// Animaciones de elementos decorativos
function animateDecorations() {
    const decorations = document.querySelectorAll('.decoration');
    decorations.forEach((decoration, index) => {
        decoration.style.animationDelay = `${index * 0.5}s`;
    });
}

// Efectos de hover en los botones
function addButtonEffects() {
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('mouseover', () => {
            button.classList.add('animate__pulse');
        });
        
        button.addEventListener('mouseout', () => {
            button.classList.remove('animate__pulse');
        });
    });
}

// Actualizar tema según la temporada
function updateSeasonalTheme() {
    const now = new Date();
    const month = now.getMonth();
    
    if (month === 11) { // Diciembre
        document.documentElement.style.setProperty('--primary-color', '#d42426');
        document.documentElement.style.setProperty('--secondary-color', '#2C5530');
    } else if (month === 0) { // Enero
        document.documentElement.style.setProperty('--primary-color', '#1E88E5');
        document.documentElement.style.setProperty('--secondary-color', '#0D47A1');
    }
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    createSnowflakes();
    animateDecorations();
    addButtonEffects();
    updateSeasonalTheme();
    
    // Validación en tiempo real
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                const formData = new FormData(form);
                const errors = validateForm(formData);
                
                if (errors.length > 0) {
                    input.classList.add('error');
                    input.title = errors.join('\n');
                } else {
                    input.classList.remove('error');
                    input.title = '';
                }
            });
        });
    });

    // Verificar si hay un código de grupo en la URL
    const urlParams = new URLSearchParams(window.location.search);
    const groupCode = urlParams.get('groupCode');
    if (groupCode) {
        document.querySelector('[name="groupCode"]').value = groupCode;
    }
});
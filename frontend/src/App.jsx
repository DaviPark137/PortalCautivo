import { useEffect, useState } from 'react';
import './App.css';
import axios from 'axios';
import logoImg from './assets/logo.png'; 
import fondoImg from './assets/fondo.jpeg'; 

const content = {
  ES: {
    title: "Acceso Wi-Fi",
    subtitle: "Bienvenido a PlataformaParkGDL. Por favor, registre sus datos para obtener acceso a la red.",
    nameLabel: "Nombre Completo",
    namePlaceholder: "Ej. Juan Pérez",
    emailLabel: "Correo Electrónico",
    emailPlaceholder: "ejemplo@correo.com",
    reasonLabel: "Motivo de visita",
    reasonPlaceholder: "Seleccione una opción",
    companyLabel: "Empresa",
    companyPlaceholder: "Seleccione la empresa",
    button: "Conectar a Internet",
    termsPre: "Al conectarse, acepta los ",
    termsLink: "Términos de Uso",
    termsPost: " de la red."
  },
  EN: {
    title: "Wi-Fi Access",
    subtitle: "Welcome to PlataformaParkGDL. Please register your details to get network access.",
    nameLabel: "Full Name",
    namePlaceholder: "e.g. John Doe",
    emailLabel: "Email Address",
    emailPlaceholder: "example@email.com",
    reasonLabel: "Reason for visit",
    reasonPlaceholder: "Select an option",
    companyLabel: "Company",
    companyPlaceholder: "Select your company",
    button: "Connect to Internet",
    termsPre: "By connecting, you accept the network ",
    termsLink: "Terms of Use",
    termsPost: "."
  }
};

function App() {
  const [lang, setLang] = useState('ES');
  const [clientMac, setClientMac] = useState('');
  const [baseGrantUrl, setBaseGrantUrl] = useState('');
  const [userContinueUrl, setUserContinueUrl] = useState('');
  
  const [formData, setFormData] = useState({
    nombre: '', email: '', motivo: '', empresa: ''
  });

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    setClientMac(urlParams.get('client_mac') || '');
    setBaseGrantUrl(urlParams.get('base_grant_url') || '');
    setUserContinueUrl(urlParams.get('user_continue_url') || 'https://google.com');
  }, []);

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleConnect = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post('http://localhost:8000/api/registro/', {
        nombre: formData.nombre,
        email: formData.email,
        motivo: formData.motivo,
        empresa: formData.empresa,
        clientMac: clientMac
      });

      if (response.status === 201) {
        
        if (baseGrantUrl) {
          window.location.href = `${baseGrantUrl}?continue_url=${encodeURIComponent(userContinueUrl)}`;
        } else {
          console.log("Guardado en PostgreSQL:", response.data);
          alert("¡Registro guardado en BD! Simulación de internet liberado (Modo Local).");
        }
      }
    } catch (error) {
      console.error("Error conectando con la base de datos:", error);
      alert("Hubo un error de comunicación con el servidor. Por favor, intenta de nuevo.");
    }
  };

  const t = content[lang];

  return (
    <div 
      className="portal-container" 
      style={{ '--bg-image': `url(${fondoImg})` }}
    >
      <div className="portal-card">
        
        <div className="header-section">
          <img src={logoImg} alt="Plataforma Park Logo" className="logo" />
          
          <div className="lang-toggle" onClick={() => setLang(lang === 'ES' ? 'EN' : 'ES')}>
            <span className={lang === 'EN' ? 'active' : ''}>EN</span>
            <span className="separator"> | </span>
            <span className={lang === 'ES' ? 'active' : ''}>ES</span>
          </div>
        </div>

        <div className="titles">
          <h1>{t.title}</h1>
          <p>{t.subtitle}</p>
        </div>

        <form onSubmit={handleConnect}>
          <div className="form-group">
            <label>{t.nameLabel}</label>
            <input type="text" name="nombre" className="form-control" placeholder={t.namePlaceholder} value={formData.nombre} onChange={handleInputChange} required />
          </div>

          <div className="form-group">
            <label>{t.emailLabel}</label>
            <input type="email" name="email" className="form-control" placeholder={t.emailPlaceholder} value={formData.email} onChange={handleInputChange} required />
          </div>

          <div className="form-group">
            <label>{t.reasonLabel}</label>
            <select name="motivo" className="form-control" value={formData.motivo} onChange={handleInputChange} required>
              <option value="" disabled>{t.reasonPlaceholder}</option>
              <option value="visita">Visita General / Visit</option>
              <option value="proveedor">Proveedor / Supplier</option>
              <option value="entrevista">Entrevista / Interview</option>
            </select>
          </div>

          <div className="form-group">
            <label>{t.companyLabel}</label>
            <select name="empresa" className="form-control" value={formData.empresa} onChange={handleInputChange} required>
              <option value="" disabled>{t.companyPlaceholder}</option>
              <option value="empresa1">Empresa 1</option>
              <option value="empresa2">Empresa 2</option>
            </select>
          </div>

          <button type="submit" className="submit-btn">{t.button}</button>
        </form>

        <div className="terms">
          {t.termsPre}<a href="#">{t.termsLink}</a>{t.termsPost}
        </div>

      </div>
    </div>
  );
}

export default App;
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
    otherReasonLabel: "Especifique su motivo de visita",
    otherReasonPlaceholder: "Escriba su motivo",
    companyLabel: "Empresa",
    companyPlaceholder: "Seleccione la empresa",
    otherCompanyLabel: "Especifique la empresa que visita",
    otherCompanyPlaceholder: "Escriba el nombre de la empresa",
    button: "Conectar a Internet",
    termsPre: "Al conectarse, acepta los ",
    termsLink: "Términos de Uso",
    termsPost: " de la red.",
    tcTitle: "Términos y Condiciones",
    tcIntro: "Al conectarse a la red Wi-Fi de PlataformaParkGDL, usted acepta los siguientes términos:",
    tcRulesTitle: "1. Uso Adecuado de la Red",
    tcRulesText: "Queda estrictamente prohibido el uso de esta red para visitar, descargar, compartir o distribuir contenido ilegal, sitios que promuevan la violencia o cualquier material protegido por derechos de autor sin autorización.",
    tcDataTitle: "2. Uso de Datos Personales",
    tcDataText: "Los datos recopilados en este formulario (nombre, correo electrónico, motivo de visita y empresa) podrán ser utilizados para fines comerciales, estadísticos y de marketing por PlataformaPark.",
    tcLiabilityTitle: "3. Exención de Responsabilidad y Límites",
    tcLiabilityText: "Este servicio de Wi-Fi se proporciona 'tal cual', sin garantías de velocidad, seguridad o disponibilidad continua. PlataformaPark no se hace responsable por pérdida de datos, daños a dispositivos o intercepciones de información que pudieran ocurrir durante su conexión.",
    tcAccept: "Entendido",
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
    otherReasonLabel: "Please specify your reason for visit",
    otherReasonPlaceholder: "Type your reason",
    companyLabel: "Company",
    companyPlaceholder: "Select your company",
    otherCompanyLabel: "Please specify the company you are visiting",
    otherCompanyPlaceholder: "Type the company name",
    button: "Connect to Internet",
    termsPre: "By connecting, you accept the network ",
    termsLink: "Terms of Use",
    termsPost: ".",
    tcTitle: "Terms and Conditions",
    tcIntro: "By connecting to the PlataformaParkGDL Wi-Fi network, you agree to the following terms:",
    tcRulesTitle: "1. Acceptable Use Policy",
    tcRulesText: "It is strictly prohibited to use this network to visit, download, share, or distribute illegal content, sites that promote violence, or any unauthorized copyrighted material.",
    tcDataTitle: "2. Use of Personal Data",
    tcDataText: "The data collected in this form (name, email, reason for visit, and company) may be used for commercial, statistical, and marketing purposes by PlataformaPark.",
    tcLiabilityTitle: "3. Disclaimer of Liability & Service Limits",
    tcLiabilityText: "This Wi-Fi service is provided 'as is', with no guarantees of speed, security, or continuous availability. PlataformaPark is not liable for data loss, device damage, or information interception that may occur during your connection.",
    tcAccept: "Understood",
  }
};

function App() {
  const [lang, setLang] = useState('ES');
  const [clientMac, setClientMac] = useState('');
  const [baseGrantUrl, setBaseGrantUrl] = useState('');
  const [userContinueUrl, setUserContinueUrl] = useState('');
  
  const [isTermsOpen, setIsTermsOpen] = useState(false);

  const [formData, setFormData] = useState({
    nombre: '', email: '', motivo: '', motivoOtro: '', empresa: '', empresaOtro: ''
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

    const finalMotivo = formData.motivo === 'otro' ? formData.motivoOtro : formData.motivo;
    const finalEmpresa = formData.empresa === 'otro' ? formData.empresaOtro : formData.empresa;

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${apiUrl}/api/registro/`, {
        nombre: formData.nombre,
        email: formData.email,
        motivo: finalMotivo,
        empresa: finalEmpresa,
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
        
        <div className="top-bar">
          <div className="lang-toggle" onClick={() => setLang(lang === 'ES' ? 'EN' : 'ES')}>
            <span className={lang === 'EN' ? 'active' : ''}>EN</span>
            <span className="separator"> | </span>
            <span className={lang === 'ES' ? 'active' : ''}>ES</span>
          </div>
        </div>

        <div className="logo-container">
          <img src={logoImg} alt="Plataforma Park Logo" className="logo" />
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
              <option value="visita">Visita General / Visitor</option>
              <option value="proveedor">Proveedor / Supplier</option>
              <option value="entrevista">Entrevista / Interview</option>
              <option value="otro">Otro / Other</option>
            </select>
          </div>

          {formData.motivo === 'otro' && (
            <div className="form-group">
              <label>{t.otherReasonLabel}</label>
              <input type="text" name="motivoOtro" className="form-control" placeholder={t.otherReasonPlaceholder} value={formData.motivoOtro} onChange={handleInputChange} required />
            </div>
          )}

          <div className="form-group">
            <label>{t.companyLabel}</label>
            <select name="empresa" className="form-control" value={formData.empresa} onChange={handleInputChange} required>
              <option value="" disabled>{t.companyPlaceholder}</option>
              <option value="PlataformaPark">PlataformaPark</option>
              <option value="MercadoLibre">MercadoLibre</option>
              <option value="Italika">Italika</option>
              <option value="RealTruck">RealTruck</option>
              <option value="Foxxcon">Foxxcon</option>
              <option value="otro">Otro / Other</option>
            </select>
          </div>

          {formData.empresa === 'otro' && (
            <div className="form-group">
              <label>{t.otherCompanyLabel}</label>
              <input type="text" name="empresaOtro" className="form-control" placeholder={t.otherCompanyPlaceholder} value={formData.empresaOtro} onChange={handleInputChange} required />
            </div>
          )}

          <button type="submit" className="submit-btn">{t.button}</button>
        </form>

        <div className="terms">
          {t.termsPre}
          <a href="#" onClick={(e) => { e.preventDefault(); setIsTermsOpen(true); }}>
            {t.termsLink}
          </a>
          {t.termsPost}
        </div>

      </div>

      {isTermsOpen && (
        <div className="modal-overlay" onClick={() => setIsTermsOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{t.tcTitle}</h2>
              <button className="modal-close" onClick={() => setIsTermsOpen(false)}>&times;</button>
            </div>
            <div className="modal-body">
              <p>{t.tcIntro}</p>
              
              <h3>{t.tcRulesTitle}</h3>
              <p>{t.tcRulesText}</p>

              <h3>{t.tcDataTitle}</h3>
              <p>{t.tcDataText}</p>

              <h3>{t.tcLiabilityTitle}</h3>
              <p>{t.tcLiabilityText}</p>
            </div>
            <div className="modal-footer">
              <button className="modal-btn" onClick={() => setIsTermsOpen(false)}>
                {t.tcAccept}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;
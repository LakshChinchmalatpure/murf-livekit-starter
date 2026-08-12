'use client';

import { useState, useEffect, useRef } from 'react';
import { ConnectionState } from 'livekit-client';
import { 
  useSessionContext, 
  useVoiceAssistant, 
  useTrackVolume, 
  useSessionMessages,
  useLocalParticipant,
  useChat
} from '@livekit/components-react';
import { 
  Mic, 
  Volume2, 
  PhoneOff, 
  Loader2, 
  ShieldCheck, 
  ShieldAlert,
  AlertTriangle, 
  MessageSquare,
  VolumeX,
  Languages
} from 'lucide-react';

interface ViewControllerProps {
  appConfig: any;
}

type LanguageCode = 'en' | 'hi' | 'hinglish';

// High-fidelity UI translations
const translations = {
  en: {
    title: 'ARTHA SAATHI',
    subtitle: 'AI Financial Services Assistant',
    navHome: 'Home',
    navSchemes: 'Government Schemes',
    navFraud: 'Fraud Awareness',
    navLiteracy: 'Financial Literacy',
    navEscalations: 'Escalations',
    heroTagline: 'Financial guidance, made simple.',
    heroDesc: 'Ask questions about banking, government schemes, digital payments, and financial safety through a natural voice conversation.',
    safetyWarning: 'Never share OTPs, PINs, passwords, or CVVs.',
    cardReadyTitle: 'READY',
    cardReadyDesc: 'Start a conversation with Artha Saathi.',
    btnStart: 'Start Conversation',
    cardConnectingTitle: 'CONNECTING',
    cardConnectingDesc: 'Connecting you to Artha Saathi...',
    cardConnectingWait: 'Please wait a moment.',
    btnConnecting: 'Connecting...',
    cardEndedTitle: 'CALL ENDED',
    cardEndedDesc: 'Your conversation has ended.',
    btnAgain: 'Start Again',
    activeTitle: 'CALL ACTIVE',
    listeningTitle: 'LISTENING TO YOU',
    listeningDesc: "Go ahead, I'm listening.",
    speakingTitle: 'ARTHA SAATHI IS SPEAKING',
    speakingDesc: "I'm responding...",
    btnEndCall: 'END CALL',
    transcriptTitle: 'Live Transcript',
    transcriptEmpty: 'No messages yet. Speak to begin.',
    transcriptSenderUser: 'You',
    transcriptSenderAgent: 'Artha Saathi',
    guidelinesTitle: 'Financial Safety Guidelines',
    guideline1: 'Never share OTPs or PINs with anyone, including bank representatives or assistants.',
    guideline2: 'Verify suspicious messages and links carefully before clicking or sending money.',
    guideline3: 'Use official bank and government channels to complete transactions and applications.',
    topicsTitle: 'Secondary Topics to Explore',
    topicSchemesTitle: 'Government Schemes',
    topicSchemesDesc: 'Understand scheme benefits and eligibility.',
    topicBasicsTitle: 'Banking Basics',
    topicBasicsDesc: 'Learn common banking terms and processes.',
    topicUpiTitle: 'UPI Safety',
    topicUpiDesc: 'Learn how to stay safe from payment fraud.',
    topicFraudTitle: 'Fraud Awareness',
    topicFraudDesc: 'Recognize common financial scams.',
    micErrorTitle: 'Microphone access is blocked',
    micErrorDesc: 'Artha Saathi needs microphone access to hear you.',
    micStep1: 'Open your browser\'s site permissions.',
    micStep2: 'Allow microphone access.',
    micStep3: 'Refresh the page.',
    micStep4: 'Start the conversation again.',
    btnTryAgain: 'Try Again',
    footerCopyright: '© 2026 Artha Saathi. All rights reserved.',
    footerLivekit: 'Built with LiveKit',
    footerRole: 'Educational Financial Literacy Assistant'
  },
  hi: {
    title: 'अर्थ साथी',
    subtitle: 'एआई वित्तीय सेवा सहायक',
    navHome: 'होम',
    navSchemes: 'सरकारी योजनाएं',
    navFraud: 'धोखाधड़ी जागरूकता',
    navLiteracy: 'वित्तीय साक्षरता',
    navEscalations: 'एस्केलेशन',
    heroTagline: 'वित्तीय मार्गदर्शन, हुआ आसान।',
    heroDesc: 'एक सहज आवाज़ बातचीत के माध्यम से बैंकिंग, सरकारी योजनाओं, डिजिटल भुगतान और धोखाधड़ी सुरक्षा के बारे में प्रश्न पूछें।',
    safetyWarning: 'ओटीपी (OTP), पिन (PIN), पासवर्ड या सीवीवी (CVV) कभी किसी से साझा न करें।',
    cardReadyTitle: 'तैयार',
    cardReadyDesc: 'अर्थ साथी के साथ बातचीत शुरू करें।',
    btnStart: 'बातचीत शुरू करें',
    cardConnectingTitle: 'कनेक्ट हो रहा है',
    cardConnectingDesc: 'आपको अर्थ साथी से कनेक्ट किया जा रहा है...',
    cardConnectingWait: 'कृपया कुछ क्षण प्रतीक्षा करें।',
    btnConnecting: 'कनेक्ट हो रहा है...',
    cardEndedTitle: 'कॉल समाप्त',
    cardEndedDesc: 'आपकी बातचीत समाप्त हो गई है।',
    btnAgain: 'पुनः प्रारंभ करें',
    activeTitle: 'कॉल सक्रिय है',
    listeningTitle: 'आपकी आवाज़ सुन रहे हैं',
    listeningDesc: 'बोलिए, मैं सुन रही हूँ।',
    speakingTitle: 'अर्थ साथी बोल रहे हैं',
    speakingDesc: 'मैं जवाब दे रही हूँ...',
    btnEndCall: 'कॉल समाप्त करें',
    transcriptTitle: 'लाइव ट्रांसक्रिप्ट',
    transcriptEmpty: 'अभी तक कोई संदेश नहीं है। शुरू करने के लिए बोलें।',
    transcriptSenderUser: 'आप',
    transcriptSenderAgent: 'अर्थ साथी',
    guidelinesTitle: 'वित्तीय सुरक्षा दिशानिर्देश',
    guideline1: 'बैंक प्रतिनिधियों या सहायकों सहित किसी के साथ भी कभी भी ओटीपी (OTP) या पिन (PIN) साझा न करें।',
    guideline2: 'पैसे भेजने या क्लिक करने से पहले संदिग्ध संदेशों और लिंक की सावधानीपूर्वक जांच करें।',
    guideline3: 'लेन-देन और आवेदन पूरा करने के लिए केवल आधिकारिक बैंक और सरकारी चैनलों का उपयोग करें।',
    topicsTitle: 'अन्वेषण करने के लिए माध्यमिक विषय',
    topicSchemesTitle: 'सरकारी योजनाएं',
    topicSchemesDesc: 'योजना के लाभ और पात्रता को समझें।',
    topicBasicsTitle: 'बैंकिंग की बुनियादी बातें',
    topicBasicsDesc: 'सामान्य बैंकिंग शब्दों और प्रक्रियाओं को जानें।',
    topicUpiTitle: 'यूपीईआई सुरक्षा',
    topicUpiDesc: 'भुगतान धोखाधड़ी से सुरक्षित रहने का तरीका जानें।',
    topicFraudTitle: 'धोखाधड़ी के प्रति जागरूकता',
    topicFraudDesc: 'सामान्य वित्तीय घोटालों को पहचानें।',
    micErrorTitle: 'माइक्रोफ़ोन एक्सेस ब्लॉक है',
    micErrorDesc: 'आपकी आवाज़ सुनने के लिए अर्थ साथी को माइक्रोफ़ोन एक्सेस की आवश्यकता है।',
    micStep1: 'अपने ब्राउज़र की साइट अनुमतियां (permissions) खोलें।',
    micStep2: 'माइक्रोफ़ोन एक्सेस की अनुमति (Allow) दें।',
    micStep3: 'पेज को रीफ्रेश करें।',
    micStep4: 'बातचीत फिर से शुरू करें।',
    btnTryAgain: 'पुनः प्रयास करें',
    footerCopyright: '© 2026 अर्थ साथी। सर्वाधिकार सुरक्षित।',
    footerLivekit: 'लाइवकिट (LiveKit) द्वारा निर्मित',
    footerRole: 'शैक्षणिक वित्तीय साक्षरता सहायक'
  },
  hinglish: {
    title: 'ARTHA SAATHI',
    subtitle: 'AI Financial Services Assistant',
    navHome: 'Home',
    navSchemes: 'Government Schemes',
    navFraud: 'Fraud Awareness',
    navLiteracy: 'Financial Literacy',
    navEscalations: 'Escalations',
    heroTagline: 'Financial guidance, made simple.',
    heroDesc: 'Natural voice conversation ke through banking, government schemes, digital payments, aur fraud safety ke baare mein sawaal puchein.',
    safetyWarning: 'OTP, PIN, password ya CVV kabhi kisi se share na karein.',
    cardReadyTitle: 'READY',
    cardReadyDesc: 'Artha Saathi ke sath baat-cheet shuru karein.',
    btnStart: 'Baat-cheet Shuru Karein',
    cardConnectingTitle: 'CONNECTING',
    cardConnectingDesc: 'Aapko Artha Saathi se connect kiya ja raha hai...',
    cardConnectingWait: 'Please thodi der wait karein.',
    btnConnecting: 'Connecting...',
    cardEndedTitle: 'CALL ENDED',
    cardEndedDesc: 'Aapki baat-cheet khatam ho gayi hai.',
    btnAgain: 'Shuru Se Shuru Karein',
    activeTitle: 'CALL ACTIVE',
    listeningTitle: 'AAPKI AWAAZ SUN RAHE HAIN',
    listeningDesc: 'Boliye, main sun rahi hoon.',
    speakingTitle: 'ARTHA SAATHI BOL RAHI HAI',
    speakingDesc: 'Main reply kar rahi hoon...',
    btnEndCall: 'CALL END KAREIN',
    transcriptTitle: 'Live Transcript',
    transcriptEmpty: 'Abhi tak koi message nahi hai. Bolna shuru karein.',
    transcriptSenderUser: 'Aap',
    transcriptSenderAgent: 'Artha Saathi',
    guidelinesTitle: 'Financial Safety Guidelines',
    guideline1: 'Bank representatives ya assistants ke sath bhi apna OTP ya PIN share na karein.',
    guideline2: 'Kisi link par click karne ya paise bejne se pehle suspicious messages ko verify karein.',
    guideline3: 'Transactions aur applications ke liye official bank aur government channels ka use karein.',
    topicsTitle: 'Secondary Topics to Explore',
    topicSchemesTitle: 'Government Schemes',
    topicSchemesDesc: 'Scheme ke benefits aur eligibility samjhein.',
    topicBasicsTitle: 'Banking Basics',
    topicBasicsDesc: 'Banking terms aur processes seekhein.',
    topicUpiTitle: 'UPI Safety',
    topicUpiDesc: 'Payment fraud se bachne ka tareeqa seekhein.',
    topicFraudTitle: 'Fraud Awareness',
    topicFraudDesc: 'Common financial scams ko pehchanein.',
    micErrorTitle: 'Microphone access blocked hai',
    micErrorDesc: 'Aapki awaaz sunne ke liye Artha Saathi ko microphone access chahiye.',
    micStep1: 'Apne browser ki site permissions open karein.',
    micStep2: 'Microphone access allow karein.',
    micStep3: 'Page ko refresh karein.',
    micStep4: 'Conversation dobara shuru karein.',
    btnTryAgain: 'Dobara Try Karein',
    footerCopyright: '© 2026 Artha Saathi. All rights reserved.',
    footerLivekit: 'Built with LiveKit',
    footerRole: 'Educational Financial Literacy Assistant'
  }
};

// Subtle reactive waveform component
function Waveform({ isActive, color = '#3b82f6', count = 9, volume = 0 }: { isActive: boolean; color?: string; count?: number; volume?: number }) {
  const [randomHeights, setRandomHeights] = useState<number[]>([]);

  useEffect(() => {
    if (isActive && volume === 0) {
      const interval = setInterval(() => {
        setRandomHeights(Array.from({ length: count }).map(() => Math.random() * 0.6 + 0.2));
      }, 100);
      return () => clearInterval(interval);
    }
  }, [isActive, volume, count]);

  return (
    <div className="flex items-center gap-1.5 h-10 justify-center">
      {Array.from({ length: count }).map((_, i) => {
        let scaleY = 0.15;
        if (isActive) {
          if (volume > 0) {
            // scale bars reactive to actual voice volume
            scaleY = 0.2 + (volume * 2.0);
            if (scaleY > 1) scaleY = 1;
          } else {
            scaleY = randomHeights[i] || 0.2;
          }
        }
        
        return (
          <div
            key={i}
            className="w-1.5 rounded-full transition-all duration-150"
            style={{
              height: '100%',
              backgroundColor: color,
              transform: `scaleY(${scaleY})`,
            }}
          />
        );
      })}
    </div>
  );
}

// Separate component for active call to ensure LiveKit hooks are only called when connected
function ActiveVoiceCard({
  session,
  appConfig,
  onDisconnect,
  chatOpen,
  setChatOpen,
  lang
}: {
  session: any;
  appConfig: any;
  onDisconnect: () => void;
  chatOpen: boolean;
  setChatOpen: (open: boolean) => void;
  lang: LanguageCode;
}) {
  const { state: agentState, audioTrack: agentAudioTrack } = useVoiceAssistant();
  const { localParticipant } = useLocalParticipant();
  const { messages } = useSessionMessages(session);
  const t = translations[lang];

  // Volumes
  const userVolume = useTrackVolume(session.local?.microphoneTrack);
  const agentVolume = useTrackVolume(agentAudioTrack);

  const [isMuted, setIsMuted] = useState(false);

  // Synchronize mute state
  useEffect(() => {
    if (localParticipant) {
      setIsMuted(!localParticipant.isMicrophoneEnabled);
    }
  }, [localParticipant, localParticipant?.isMicrophoneEnabled]);

  const toggleMute = async () => {
    if (localParticipant) {
      const currentlyEnabled = localParticipant.isMicrophoneEnabled;
      await localParticipant.setMicrophoneEnabled(!currentlyEnabled);
      setIsMuted(currentlyEnabled);
    }
  };

  const [textInput, setTextInput] = useState('');
  const { send, isSending } = useChat();

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim() || isSending) return;
    try {
      await send(textInput.trim());
      setTextInput('');
    } catch (err) {
      console.error('Failed to send text message:', err);
    }
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, chatOpen]);

  const activeState = (agentState === 'speaking' || agentState === 'thinking') ? 'speaking' : 'listening';

  return (
    <div className="w-full flex flex-col items-center">
      {/* CENTRAL VOICE ORB */}
      <div className="relative mb-6">
        {/* Pulsing ring aura */}
        <div 
          className={`absolute inset-0 rounded-full border transition-all duration-500 scale-105 ${
            activeState === 'listening' 
              ? 'border-emerald-500/40 shadow-[0_0_25px_rgba(16,185,129,0.3)] animate-ping'
              : 'border-primary/40 shadow-[0_0_25px_rgba(59,130,246,0.3)] animate-pulse'
          }`} 
        />

        {/* Outer border ring */}
        <div className={`p-1.5 rounded-full border-2 transition-all duration-300 ${
          activeState === 'listening' ? 'border-emerald-500' : 'border-primary'
        }`}>
          {/* Image Orb */}
          <div className="size-32 rounded-full overflow-hidden bg-muted relative flex items-center justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img 
              src="/artha-saathi-avatar.png" 
              alt="Artha Saathi Avatar" 
              className="size-full object-cover select-none"
            />
          </div>
        </div>
      </div>

      {/* ACTIVE SPEAKER STATE WAVEFORMS */}
      <div className="w-full max-w-xs h-12 mb-6 flex flex-col justify-center">
        {activeState === 'listening' ? (
          <Waveform isActive={true} color="#10b981" count={11} volume={userVolume} />
        ) : (
          <Waveform isActive={true} color="#3b82f6" count={11} volume={agentVolume} />
        )}
      </div>

      {/* STATUS TEXT & INSTRUCTIONS */}
      <div className="space-y-2 mb-8 min-h-16 flex flex-col justify-center text-center">
        {activeState === 'listening' ? (
          <>
            <h4 className="font-bold text-lg text-emerald-600 dark:text-emerald-500 uppercase tracking-wider flex items-center justify-center gap-2">
              <Mic className="size-4 shrink-0" />
              {t.listeningTitle}
            </h4>
            <p className="text-sm text-muted-foreground">{t.listeningDesc}</p>
          </>
        ) : (
          <>
            <h4 className="font-bold text-lg text-primary uppercase tracking-wider flex items-center justify-center gap-2">
              <Volume2 className="size-4 shrink-0" />
              {t.speakingTitle}
            </h4>
            <p className="text-sm text-muted-foreground">{t.speakingDesc}</p>
          </>
        )}
      </div>

      {/* ACTIVE CALL CONTROL HUD */}
      <div className="w-full max-w-xs space-y-4">
        <div className="flex items-center justify-center gap-3">
          {/* Microphone Toggle */}
          <button
            onClick={toggleMute}
            className={`p-3 rounded-xl border transition-all cursor-pointer ${
              isMuted
                ? 'bg-destructive/10 border-destructive/20 text-destructive hover:bg-destructive/20'
                : 'bg-muted border-border hover:bg-muted/80 text-foreground'
            }`}
            title={isMuted ? 'Unmute Microphone' : 'Mute Microphone'}
            aria-label={isMuted ? 'Unmute Microphone' : 'Mute Microphone'}
          >
            {isMuted ? <VolumeX className="size-5" /> : <Mic className="size-5" />}
          </button>

          {/* End Call Button */}
          <button
            onClick={onDisconnect}
            className="bg-destructive hover:bg-destructive/90 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-sm hover:shadow flex items-center gap-2 cursor-pointer text-xs uppercase tracking-wider"
          >
            <PhoneOff className="size-4 shrink-0" />
            {t.btnEndCall}
          </button>

          {/* Chat Transcript Toggle */}
          {appConfig.supportsChatInput !== false && (
            <button
              onClick={() => setChatOpen(!chatOpen)}
              className={`p-3 rounded-xl border transition-all cursor-pointer ${
                chatOpen
                  ? 'bg-primary/10 border-primary/20 text-primary hover:bg-primary/20'
                  : 'bg-muted border-border hover:bg-muted/80 text-foreground'
              }`}
              title="Toggle Conversation Transcript"
              aria-label="Toggle Conversation Transcript"
            >
              <MessageSquare className="size-5" />
            </button>
          )}
        </div>
      </div>

      
      {/* COLLAPSIBLE TRANSCRIPT AREA */}
      {chatOpen && (
        <div className="w-full mt-6 border-t border-border/50 bg-muted/10 px-6 py-4 flex flex-col gap-3 text-left">
          <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
            {t.transcriptTitle}
          </h4>
          
          <div className="max-h-56 overflow-y-auto space-y-3 [scrollbar-width:thin] pr-1">
            {messages.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">{t.transcriptEmpty}</p>
            ) : (
              <div className="space-y-2 text-xs">
                {messages.map((msg: any, i: number) => {
                  const isUser = msg.from?.isLocal === true;
                  return (
                    <div key={i} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                      <span className="text-[9px] font-bold text-muted-foreground mb-0.5">
                        {isUser ? t.transcriptSenderUser : t.transcriptSenderAgent}
                      </span>
                      <div className={`px-3 py-2 rounded-xl max-w-[85%] ${
                        isUser 
                          ? 'bg-primary text-white rounded-tr-none shadow-sm' 
                          : 'bg-card border border-border text-foreground rounded-tl-none shadow-sm'
                      }`}>
                        {msg.message}
                      </div>
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Text Conversation Input Form */}
          <form 
            onSubmit={handleSendMessage}
            className="flex items-center gap-2 mt-1 pt-3 border-t border-border/60"
          >
            <input
              type="text"
              placeholder="Type your message here..."
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              className="flex-1 bg-card border border-border rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary text-foreground placeholder:text-muted-foreground"
              disabled={isSending}
            />
            <button
              type="submit"
              disabled={isSending || !textInput.trim()}
              className="bg-primary hover:bg-primary/95 text-white font-bold p-2 px-4 rounded-xl text-xs disabled:opacity-50 transition-all cursor-pointer shadow-sm"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const session = useSessionContext();
  const { isConnected, start, connectionState, end } = session;
  const [hasConnectedOnce, setHasConnectedOnce] = useState(false);
  const [micBlocked, setMicBlocked] = useState(false);
  const [isCheckingMic, setIsCheckingMic] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>('en');
  const [chatOpen, setChatOpen] = useState(false);

  const t = translations[selectedLanguage];

  // Sync connection state history
  useEffect(() => {
    if (isConnected) {
      setHasConnectedOnce(true);
    }
  }, [isConnected]);

  // Check microphone permissions and start session
  const startConversation = async () => {
    setIsCheckingMic(true);
    setMicBlocked(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop checking stream
      stream.getTracks().forEach((track) => track.stop());
      setIsCheckingMic(false);
      
      if (hasConnectedOnce && !isConnected) {
        setHasConnectedOnce(false);
      }
      
      await start();
    } catch (error: any) {
      console.error('Microphone permission check failed:', error);
      setIsCheckingMic(false);
      setMicBlocked(true);
    }
  };

  const handleStartAgain = async () => {
    setMicBlocked(false);
    setHasConnectedOnce(false);
    await startConversation();
  };

  const handleDisconnect = async () => {
    if (typeof end === 'function') {
      await end();
    }
  };

  // Determine current active state for display mapping
  let activeState: 'ready' | 'connecting' | 'listening' | 'speaking' | 'ended' = 'ready';

  if (connectionState === ConnectionState.Connecting || isCheckingMic) {
    activeState = 'connecting';
  } else if (isConnected) {
    // Handled internally in ActiveVoiceCard component to maintain hook rules
  } else if (hasConnectedOnce) {
    activeState = 'ended';
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans w-full max-w-7xl mx-auto px-4 md:px-8 py-6">
      
      {/* HEADER SECTION */}
      <header className="border-b border-border/60 pb-5 mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          {/* Logo/Icon */}
          <div className="bg-primary/10 p-2.5 rounded-xl border border-primary/20 shadow-sm">
            <ShieldCheck className="size-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              {t.title}
            </h1>
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
              {t.subtitle}
            </p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm font-semibold text-muted-foreground items-center">
          <a href="#" className="text-primary hover:text-primary transition-colors">{t.navHome}</a>
          <a href="#schemes" className="hover:text-foreground transition-colors">{t.navSchemes}</a>
          <a href="#fraud" className="hover:text-foreground transition-colors">{t.navFraud}</a>
          <a href="#literacy" className="hover:text-foreground transition-colors">{t.navLiteracy}</a>
          <a href="/escalations" className="hover:text-foreground transition-colors">{t.navEscalations}</a>
        </nav>

        {/* Language Selector */}
        <div className="flex items-center gap-2 self-start sm:self-center">
          <Languages className="size-4 text-muted-foreground" />
          <div className="inline-flex rounded-lg border border-border bg-muted/50 p-0.5 text-xs font-semibold">
            <button
              onClick={() => setSelectedLanguage('en')}
              className={`px-3 py-1 rounded-md transition-all cursor-pointer ${
                selectedLanguage === 'en'
                  ? 'bg-card text-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              English
            </button>
            <button
              onClick={() => setSelectedLanguage('hi')}
              className={`px-3 py-1 rounded-md transition-all cursor-pointer ${
                selectedLanguage === 'hi'
                  ? 'bg-card text-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              हिन्दी
            </button>
            <button
              onClick={() => setSelectedLanguage('hinglish')}
              className={`px-3 py-1 rounded-md transition-all cursor-pointer ${
                selectedLanguage === 'hinglish'
                  ? 'bg-card text-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Hinglish
            </button>
          </div>
        </div>
      </header>

      {/* MAIN CONTAINER */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-8">
        
        {/* LEFT COLUMN: HERO & INFO */}
        <div className="lg:col-span-7 flex flex-col gap-8 h-full justify-between">
          <div className="space-y-6">
            {/* HERO SECTION */}
            <div className="space-y-4">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
                <span className="size-1.5 rounded-full bg-primary animate-pulse" />
                Live Voice Agent
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground leading-tight">
                {t.heroTagline}
              </h2>
              <p className="text-base text-muted-foreground max-w-xl leading-relaxed">
                {t.heroDesc}
              </p>
            </div>

            {/* SAFETY NOTICE */}
            <div className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-warning/30 bg-warning/5 text-amber-600 dark:text-amber-500 text-sm font-semibold max-w-md">
              <AlertTriangle className="size-4 shrink-0 text-amber-600" />
              <span>{t.safetyWarning}</span>
            </div>
          </div>

          {/* TOPIC CARDS SECTION */}
          <div className="mt-8 pt-8 border-t border-border/50">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-4">
              {t.topicsTitle}
            </h3>
            <div id="schemes" className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl border border-border bg-card/50 hover:bg-card hover:border-primary/30 transition-all shadow-xs group">
                <h4 className="font-bold text-sm text-foreground mb-1 group-hover:text-primary transition-colors">
                  {t.topicSchemesTitle}
                </h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {t.topicSchemesDesc}
                </p>
              </div>

              <div id="literacy" className="p-4 rounded-xl border border-border bg-card/50 hover:bg-card hover:border-primary/30 transition-all shadow-xs group">
                <h4 className="font-bold text-sm text-foreground mb-1 group-hover:text-primary transition-colors">
                  {t.topicBasicsTitle}
                </h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {t.topicBasicsDesc}
                </p>
              </div>

              <div className="p-4 rounded-xl border border-border bg-card/50 hover:bg-card hover:border-primary/30 transition-all shadow-xs group">
                <h4 className="font-bold text-sm text-foreground mb-1 group-hover:text-primary transition-colors">
                  {t.topicUpiTitle}
                </h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {t.topicUpiDesc}
                </p>
              </div>

              <div id="fraud" className="p-4 rounded-xl border border-border bg-card/50 hover:bg-card hover:border-primary/30 transition-all shadow-xs group">
                <h4 className="font-bold text-sm text-foreground mb-1 group-hover:text-primary transition-colors">
                  {t.topicFraudTitle}
                </h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {t.topicFraudDesc}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: VOICE CARD & PANEL */}
        <div className="lg:col-span-5 flex flex-col gap-6 w-full lg:sticky lg:top-6">
          
          {/* VOICE CARD CONTAINER */}
          <div className="border border-border/80 rounded-2xl bg-card shadow-md flex flex-col overflow-hidden relative">
            
            {/* Header info */}
            <div className="px-6 py-5 border-b border-border/40 bg-muted/30 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-base text-foreground tracking-tight">Artha Saathi</h3>
                <p className="text-xs text-muted-foreground">{t.subtitle}</p>
              </div>
              
              {/* Dynamic Status badge */}
              <div>
                {micBlocked && (
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider uppercase bg-destructive/10 text-destructive border border-destructive/20">
                    ERROR
                  </span>
                )}
                {!micBlocked && activeState === 'ready' && !isConnected && (
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider uppercase bg-muted text-muted-foreground border border-border">
                    {t.cardReadyTitle}
                  </span>
                )}
                {!micBlocked && activeState === 'connecting' && !isConnected && (
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider uppercase bg-warning/10 text-amber-600 dark:text-amber-500 border border-warning/20 animate-pulse">
                    {t.cardConnectingTitle}
                  </span>
                )}
                {!micBlocked && isConnected && (
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider uppercase bg-emerald-500/10 text-emerald-600 dark:text-emerald-500 border border-emerald-500/20">
                    {t.activeTitle}
                  </span>
                )}
                {!micBlocked && activeState === 'ended' && !isConnected && (
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider uppercase bg-destructive/10 text-destructive border border-destructive/20">
                    {t.cardEndedTitle}
                  </span>
                )}
              </div>
            </div>

            {/* CARD CONTENT */}
            <div className="px-6 py-10 flex flex-col items-center justify-center text-center">
              
              {/* MICROPHONE ACCESS ERROR BOX */}
              {micBlocked ? (
                <div className="w-full space-y-6">
                  <div className="mx-auto size-16 rounded-full bg-destructive/10 border border-destructive/20 flex items-center justify-center text-destructive">
                    <ShieldAlert className="size-8" />
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-bold text-lg text-foreground">{t.micErrorTitle}</h4>
                    <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                      {t.micErrorDesc}
                    </p>
                  </div>
                  
                  {/* Step list */}
                  <div className="bg-muted/50 p-4 rounded-xl text-left text-xs space-y-2.5 max-w-sm mx-auto border border-border">
                    <div className="flex gap-2">
                      <span className="font-bold text-primary">1.</span>
                      <span className="text-muted-foreground">{t.micStep1}</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="font-bold text-primary">2.</span>
                      <span className="text-muted-foreground">{t.micStep2}</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="font-bold text-primary">3.</span>
                      <span className="text-muted-foreground">{t.micStep3}</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="font-bold text-primary">4.</span>
                      <span className="text-muted-foreground">{t.micStep4}</span>
                    </div>
                  </div>

                  <button
                    onClick={startConversation}
                    className="w-full max-w-xs bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3 px-6 rounded-xl transition-all shadow-sm flex items-center justify-center gap-2 mx-auto cursor-pointer"
                  >
                    {t.btnTryAgain}
                  </button>
                </div>
              ) : (
                <div className="w-full flex flex-col items-center">
                  
                  {isConnected ? (
                    /* RENDERED ONLY WHEN CONNECTED (SSR SAFE & ROOM HOOKS SAFE) */
                    <ActiveVoiceCard 
                      session={session} 
                      appConfig={appConfig} 
                      onDisconnect={handleDisconnect} 
                      chatOpen={chatOpen}
                      setChatOpen={setChatOpen}
                      lang={selectedLanguage}
                    />
                  ) : (
                    /* DISCONNECTED LIFE CYCLE RENDERS */
                    <div className="w-full flex flex-col items-center">
                      {/* CENTRAL VOICE ORB */}
                      <div className="relative mb-6">
                        <div className={`absolute inset-0 rounded-full border transition-all scale-105 ${
                          activeState === 'connecting'
                            ? 'border-warning/30 shadow-[0_0_20px_rgba(245,158,11,0.2)] animate-pulse'
                            : 'border-border'
                        }`} />

                        <div className="p-1.5 rounded-full border-2 border-border/80">
                          <div className="size-32 rounded-full overflow-hidden bg-muted relative flex items-center justify-center">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img 
                              src="/artha-saathi-avatar.png" 
                              alt="Artha Saathi Avatar" 
                              className="size-full object-cover select-none"
                            />
                            {activeState === 'connecting' && (
                              <div className="absolute inset-0 bg-black/40 flex items-center justify-center text-white">
                                <Loader2 className="size-8 animate-spin" />
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* INACTIVE WAVEFORM */}
                      <div className="w-full max-w-xs h-12 mb-6 flex flex-col justify-center">
                        <Waveform isActive={false} color="#94a3b8" count={11} volume={0} />
                      </div>

                      {/* STATUS TEXT & INSTRUCTIONS */}
                      <div className="space-y-2 mb-8 min-h-16 flex flex-col justify-center">
                        {activeState === 'ready' && (
                          <>
                            <h4 className="font-bold text-lg text-foreground uppercase tracking-wider text-muted-foreground/80">{t.cardReadyTitle}</h4>
                            <p className="text-sm text-muted-foreground">{t.cardReadyDesc}</p>
                          </>
                        )}
                        {activeState === 'connecting' && (
                          <>
                            <h4 className="font-bold text-lg text-amber-600 dark:text-amber-500 uppercase tracking-wider">{t.cardConnectingTitle}</h4>
                            <p className="text-sm text-muted-foreground">{t.cardConnectingDesc}</p>
                            <p className="text-xs text-muted-foreground/75">{t.cardConnectingWait}</p>
                          </>
                        )}
                        {activeState === 'ended' && (
                          <>
                            <h4 className="font-bold text-lg text-destructive uppercase tracking-wider">{t.cardEndedTitle}</h4>
                            <p className="text-sm text-muted-foreground">{t.cardEndedDesc}</p>
                          </>
                        )}
                      </div>

                      {/* ACTION BUTTONS */}
                      <div className="w-full max-w-xs">
                        {activeState === 'ready' && (
                          <button
                            onClick={startConversation}
                            disabled={isCheckingMic}
                            className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-bold py-3.5 px-6 rounded-xl transition-all shadow-sm hover:shadow flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                          >
                            {isCheckingMic ? <Loader2 className="size-4 animate-spin" /> : null}
                            {t.btnStart}
                          </button>
                        )}

                        {activeState === 'connecting' && (
                          <button
                            disabled
                            className="w-full bg-muted border border-border text-muted-foreground font-bold py-3.5 px-6 rounded-xl transition-all flex items-center justify-center gap-2 disabled:cursor-not-allowed text-sm"
                          >
                            <Loader2 className="size-4 animate-spin text-primary" />
                            {t.btnConnecting}
                          </button>
                        )}

                        {activeState === 'ended' && (
                          <button
                            onClick={handleStartAgain}
                            className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-bold py-3.5 px-6 rounded-xl transition-all shadow-sm hover:shadow flex items-center justify-center gap-2 cursor-pointer text-sm"
                          >
                            {t.btnAgain}
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                </div>
              )}
            </div>
          </div>

          {/* FINANCIAL SAFETY PANEL */}
          <div className="border border-border/60 bg-card rounded-2xl p-5 shadow-xs">
            <h4 className="text-sm font-extrabold text-foreground mb-3 flex items-center gap-2">
              <ShieldCheck className="size-4 text-emerald-500" />
              {t.guidelinesTitle}
            </h4>
            <ul className="text-xs space-y-2.5 font-medium text-muted-foreground leading-relaxed">
              <li className="flex items-start gap-2">
                <span className="shrink-0 text-primary">🔒</span>
                <span>{t.guideline1}</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="shrink-0 text-primary">🛡️</span>
                <span>{t.guideline2}</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="shrink-0 text-primary">🏦</span>
                <span>{t.guideline3}</span>
              </li>
            </ul>
          </div>
        </div>
      </main>

      {/* FOOTER */}
      <footer className="border-t border-border/50 pt-6 mt-8 flex flex-col md:flex-row items-center justify-between text-xs text-muted-foreground gap-4">
        <p>{t.footerCopyright}</p>
        <div className="flex gap-4">
          <a href="https://livekit.io" target="_blank" rel="noopener noreferrer" className="hover:underline">{t.footerLivekit}</a>
          <span>•</span>
          <span className="font-semibold">{t.footerRole}</span>
        </div>
      </footer>
    </div>
  );
}

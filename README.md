# 🎬 Netflix Codes Bot 🤖

<div align="center">

![Netflix Bot Banner](https://img.shields.io/badge/Netflix-Codes%20Bot-E50914?style=for-the-badge&logo=netflix&logoColor=white)

**🚀 The Ultimate Netflix Authentication Code Management System 🚀**

*Streamline your Netflix experience with automated code delivery and user management*

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28?style=flat-square&logo=firebase&logoColor=black)](https://firebase.google.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## ✨ **What Makes This Bot Special?**

> *"Your Netflix, Your Way, Your Bot!"* 🎭

This isn't just another Telegram bot – it's a **complete Netflix authentication ecosystem** that transforms how you manage Netflix access codes. Built with love, powered by Python, and designed for seamless user experience.

### 🌟 **Key Highlights**

- 🔐 **Multi-Email Management** - Support for multiple Netflix accounts per user
- 🎯 **Smart Code Delivery** - Automated sign-in, household, and temp auth codes
- 👑 **Advanced Admin Panel** - Complete user and credential management
- 🔄 **Real-time Sync** - Firebase-powered instant updates
- 🛡️ **Security First** - Role-based access control and data protection
- 📱 **Beautiful UI** - Intuitive inline keyboards and rich formatting

---

## 🎪 **Features Showcase**

<table>
<tr>
<td width="50%">

### 🎭 **For Users**
- 🔑 **Get Authentication Codes**
  - Sign-in codes
  - Household codes
  - Temporary auth codes
- 📧 **Email Selection**
  - Choose from assigned accounts
  - Smart single/multi-email handling
- 💳 **Subscription Info**
  - View active email accounts
  - Check expiration dates
  - Track subscription status

</td>
<td width="50%">

### 👑 **For Admins**
- 👤 **User Management**
  - Add/remove users
  - Update user information
  - View complete user profiles
- 📧 **Credential Management**
  - Bulk credential import
  - Individual account management
  - Email assignment to users
- 🛠️ **Advanced Tools**
  - Admin role management
  - System monitoring
  - Automated cleanup

</td>
</tr>
</table>

---

## 🚀 **Quick Start Guide**

### 📋 **Prerequisites**

```bash
🐍 Python 3.8+
🤖 Telegram Bot Token
🔥 Firebase Project
📧 Netflix Account Credentials
```

### ⚡ **Installation**

1. **Clone the Magic** ✨
   ```bash
   git clone https://github.com/yourusername/netflix-codes-bot.git
   cd netflix-codes-bot
   ```

2. **Create Virtual Environment** 🏠
   ```bash
   python -m venv env
   env\Scripts\activate  # Windows
   source env/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies** 📦
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment** ⚙️
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Launch the Bot** 🚀
   ```bash
   python bot.py
   ```

---

## 🎨 **Configuration**

### 🔧 **Environment Variables**

Create a `.env` file with the following:

```env
# 🤖 Telegram Bot Configuration
bot_token=your_telegram_bot_token_here

# 🔥 Firebase Configuration
FIREBASE_TYPE=service_account
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour_Private_Key_Here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
```

### 📊 **Database Structure**

```json
{
  "users": {
    "user_id": {
      "userid": "123456789",
      "username": "john_doe",
      "admin": false,
      "subscriber": true,
      "joined": "2025-01-15 10:30:00",
      "emails": [
        {
          "email": "netflix1@gmail.com",
          "password": "password123",
          "duration": 1738742400
        }
      ]
    }
  },
  "credentials": {
    "email@domain.com": {
      "email": "email@domain.com",
      "password": "password123"
    }
  }
}
```

---

## 🎭 **Bot Commands & Features**

### 🎪 **User Commands**

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | 🎬 Launch the bot | `/start` |
| `/add` | ➕ Add email to user | `/add 123456789 email@domain.com 30` |
| `/remove` | ➖ Remove user email | `/remove 123456789 email@domain.com` |

### 🎨 **Interactive Menus**

#### 🎭 **Main Menu**
```
✨ Choose Your Netflix Journey ✨

👑 Admin Panel 🛠         (Admins only)
🔑 Get Authentication Code 🔐
💳 Subscription Information 💳
```

#### 👑 **Admin Panel**
```
👑 Admin Panel 👑

➕ Add New User 👤
✏️ Update User Info 📝
👑 Add Admin 👤
❌ Remove User 👤
📧 Manage Credentials 📧
📨 Add User Email 📨
🗑️ Remove User Email 🗑️
👤 View User Info 👤
```

#### 🔑 **Code Selection**
```
🔐 Netflix Authentication Codes 🔐

🔑 Sign In Code
🏠 Household Code
🔐 Temporary Authentication Code
```

---

## 🏗️ **Architecture**

### 🎪 **Project Structure**

```
netflix-codes-bot/
├── 🤖 bot.py                 # Main bot application
├── 🔥 firebase_db.py         # Database operations
├── 📧 netflix_automation.py  # Netflix code automation
├── 📋 requirements.txt       # Dependencies
├── 🔧 .env                   # Environment variables
├── 📚 README.md              # This beautiful file
└── 📁 env/                   # Virtual environment
```

### 🎨 **Technology Stack**

<div align="center">

| Technology | Purpose | Version |
|------------|---------|---------|
| 🐍 **Python** | Core Language | 3.8+ |
| 🤖 **python-telegram-bot** | Telegram API | Latest |
| 🔥 **Firebase Admin SDK** | Database | Latest |
| 🌐 **Selenium** | Web Automation | Latest |
| 🔧 **python-dotenv** | Environment Management | Latest |

</div>

---

## 🎭 **Usage Examples**

### 🎪 **For Regular Users**

1. **Getting a Sign-in Code** 🔑
   ```
   User: Clicks "🔑 Get Authentication Code"
   Bot: Shows code type selection
   User: Selects "🔑 Sign In Code"
   Bot: Shows email selection (if multiple)
   User: Selects email account
   Bot: "📤 Send Code!" → Delivers Netflix code
   ```

2. **Checking Subscription** 💳
   ```
   User: Clicks "💳 Subscription Information"
   Bot: Shows all active email accounts with expiration dates
   ```

### 👑 **For Admins**

1. **Adding Bulk Credentials** 📦
   ```
   Admin: Admin Panel → "📧 Manage Credentials" → "📦 Add Multiple"
   Admin: Pastes email:password pairs
   Bot: Processes and stores all credentials
   ```

2. **Viewing User Info** 👤
   ```
   Admin: Admin Panel → "👤 View User Info"
   Admin: Enters user ID
   Bot: Shows complete user profile with all emails and details
   ```

---

## 🛡️ **Security Features**

- 🔐 **Role-Based Access Control** - Admin vs User permissions
- 🛡️ **Input Validation** - Prevents malicious inputs
- 🔒 **Secure Credential Storage** - Firebase security rules
- ⏰ **Automatic Cleanup** - Expired subscriptions removed
- 🚫 **Error Handling** - Graceful failure management

---

## 🎯 **Advanced Features**

### 🔄 **Multi-Email Management**
- **Smart Email Assignment** - Assign multiple Netflix accounts to users
- **Automatic Expiration** - Time-based access control
- **Email Selection UI** - Users choose from available accounts
- **Bulk Operations** - Mass credential import and management

### 🤖 **Automation & Intelligence**
- **Code Delivery** - Automated Netflix authentication code fetching
- **Session Management** - Persistent login sessions
- **Error Recovery** - Automatic retry mechanisms
- **Smart Notifications** - Real-time status updates

### 📊 **Analytics & Monitoring**
- **User Activity Tracking** - Monitor bot usage patterns
- **Subscription Analytics** - Track active/expired accounts
- **Performance Metrics** - Bot response times and success rates
- **Admin Dashboard** - Comprehensive system overview

---

## 🚀 **Deployment Options**

### 🐳 **Docker Deployment**
```bash
# Build the image
docker build -t netflix-codes-bot .

# Run the container
docker run -d --name netflix-bot --env-file .env netflix-codes-bot
```

### ☁️ **Cloud Deployment**
- **Heroku** - Easy one-click deployment
- **Google Cloud Run** - Serverless container deployment
- **AWS Lambda** - Event-driven execution
- **Railway** - Simple git-based deployment

### 🖥️ **Local Development**
```bash
# Development mode with auto-reload
python -m bot --dev

# Debug mode with verbose logging
python -m bot --debug
```

---

## 🤝 **Contributing**

We love contributions! Here's how you can help:

1. 🍴 **Fork the repository**
2. 🌿 **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. 💾 **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. 📤 **Push to the branch** (`git push origin feature/amazing-feature`)
5. 🎉 **Open a Pull Request**

### 🎨 **Development Guidelines**

- 📝 Follow PEP 8 style guidelines
- 🧪 Add tests for new features
- 📚 Update documentation
- 🎭 Keep the code beautiful and readable

### 🐛 **Bug Reports**

Found a bug? Please create an issue with:
- 📝 Clear description of the problem
- 🔄 Steps to reproduce
- 💻 Your environment details
- 📸 Screenshots (if applicable)

---

## 📈 **Roadmap**

### 🎯 **Upcoming Features**
- [ ] 📱 **Mobile App** - Native mobile companion
- [ ] 🌐 **Web Dashboard** - Browser-based admin panel
- [ ] 🔔 **Push Notifications** - Real-time alerts
- [ ] 📊 **Advanced Analytics** - Detailed usage statistics
- [ ] 🌍 **Multi-language Support** - International localization
- [ ] 🎨 **Custom Themes** - Personalized bot appearance

### 🔮 **Future Enhancements**
- 🤖 **AI Integration** - Smart code prediction
- 🔗 **API Endpoints** - Third-party integrations
- 📱 **Widget Support** - Embeddable components
- 🎮 **Gamification** - User engagement features

---

## 📜 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Netflix Codes Bot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🎪 **Support & Community**

<div align="center">

### 💬 **Get Help**

[![Telegram](https://img.shields.io/badge/Telegram-Support-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/your_support_channel)
[![Issues](https://img.shields.io/badge/GitHub-Issues-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/yourusername/netflix-codes-bot/issues)
[![Discussions](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/yourusername/netflix-codes-bot/discussions)

### 🌟 **Community**

Join our growing community of developers and Netflix enthusiasts!

- 💬 **Discord Server** - Real-time chat and support
- 📧 **Newsletter** - Latest updates and features
- 🐦 **Twitter** - Follow for announcements
- 📺 **YouTube** - Tutorials and demos

### ⭐ **Show Your Support**

If this project helped you, please consider:
- ⭐ **Starring** the repository
- 🍴 **Forking** for your own projects
- 📢 **Sharing** with friends and colleagues
- 💝 **Contributing** to the codebase

</div>

---

## 🏆 **Acknowledgments**

Special thanks to:

- 🤖 **python-telegram-bot** team for the amazing library
- 🔥 **Firebase** team for the robust database solution
- 🌐 **Selenium** contributors for web automation tools
- 👥 **Open Source Community** for inspiration and support
- 🎬 **Netflix** for the streaming service we all love

---

## 📊 **Statistics**

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/yourusername/netflix-codes-bot?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/netflix-codes-bot?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/yourusername/netflix-codes-bot?style=social)

![GitHub issues](https://img.shields.io/github/issues/yourusername/netflix-codes-bot)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/netflix-codes-bot)
![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/netflix-codes-bot)

</div>

---

<div align="center">

### 🎭 **Made with ❤️ for the Netflix Community**

*"Bringing Netflix codes to your fingertips, one message at a time!"*

---

**🎬 Happy Streaming! 🍿**

*Built by developers, for developers, with love for the streaming community.*

</div>

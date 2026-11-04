--------------------------------------------------------------------------------
-- SISTEMA DE GESTIÓN DE BASE DE DATOS - UNTELS
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'BD_LOGISTICA_UNTELS')
BEGIN
    CREATE DATABASE BD_LOGISTICA_UNTELS
    ON PRIMARY 
    (
        NAME = 'BD_LOGISTICA_UNTELS_Data',
        FILENAME = 'C:\BD\SQLData\BD_LOGISTICA_UNTELS.mdf',
        SIZE = 10MB, MAXSIZE = 500MB, FILEGROWTH = 5MB
    )
    LOG ON
    (
        NAME = 'BD_LOGISTICA_UNTELS_Log',
        FILENAME = 'C:\BD\SQLLogs\BD_LOGISTICA_UNTELS_log.ldf',
        SIZE = 5MB, MAXSIZE = 100MB, FILEGROWTH = 2MB
    );
END;
GO
USE BD_LOGISTICA_UNTELS;
GO
-- ============================================================================
-- VERIFICACIÓN Y CREACIÓN SEGURA DE TABLAS (Evita errores si ya existen)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[TIPO_ORDEN]') AND type in (N'U'))
BEGIN
    CREATE TABLE TIPO_ORDEN (
        Id_Tipo_Orden TINYINT IDENTITY(1,1) PRIMARY KEY,
        Codigo VARCHAR(5) NOT NULL UNIQUE,  
        Descripcion VARCHAR(50) NOT NULL
    );
END;
GO

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[ESTADO_ORDEN]') AND type in (N'U'))
BEGIN
    CREATE TABLE ESTADO_ORDEN (
        Id_Estado TINYINT IDENTITY(1,1) PRIMARY KEY,
        Nombre_Estado VARCHAR(30) NOT NULL UNIQUE 
    );
END;
GO

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[PROVEEDOR]') AND type in (N'U'))
BEGIN
    CREATE TABLE PROVEEDOR (
        RUC CHAR(11) PRIMARY KEY,
        Razon_Social VARCHAR(200) NOT NULL
    );
END;
GO
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[ORDEN]') AND type in (N'U'))
BEGIN
    CREATE TABLE ORDEN (
        Numero_Orden INT NOT NULL,
        Id_Tipo_Orden TINYINT NOT NULL,
        RUC CHAR(11) NOT NULL,
        Id_Estado TINYINT NOT NULL,
        Nro_Exp_SIAF INT NOT NULL,
        Tipo_Contratacion VARCHAR(100) DEFAULT 'NAN',
        Descripcion_Finalidad VARCHAR(MAX) NOT NULL,
        Fecha_Emision DATE NOT NULL,
        Fecha_Compromiso DATE NOT NULL,
        Monto DECIMAL(12,2) NOT NULL CONSTRAINT CK_ORDEN_Monto CHECK (Monto >= 0),
        
        CONSTRAINT PK_ORDEN PRIMARY KEY (Numero_Orden, Id_Tipo_Orden),  
        CONSTRAINT FK_ORDEN_TIPO FOREIGN KEY (Id_Tipo_Orden) REFERENCES TIPO_ORDEN(Id_Tipo_Orden),
        CONSTRAINT FK_ORDEN_PROVEEDOR FOREIGN KEY (RUC) REFERENCES PROVEEDOR(RUC),
        CONSTRAINT FK_ORDEN_ESTADO FOREIGN KEY (Id_Estado) REFERENCES ESTADO_ORDEN(Id_Estado)
    );
END;
GO
-- ============================================================================
-- CREACIÓN SEGURA DE ÍNDICES NO AGRUPADOS (Evita duplicidad)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ORDEN_RUC' AND object_id = OBJECT_ID('ORDEN'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_ORDEN_RUC ON ORDEN(RUC);
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ORDEN_FechaEmision' AND object_id = OBJECT_ID('ORDEN'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_ORDEN_FechaEmision ON ORDEN(Fecha_Emision);
END;
GO

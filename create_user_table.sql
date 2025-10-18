-- ����� ���� ���̺� ����
CREATE TABLE IF NOT EXISTS Users (
    user_id TEXT PRIMARY KEY,           -- ����� ID (��: ct0001, dt0003)
    password TEXT NOT NULL,             -- ��й�ȣ (�ؽ�ȭ)
    name TEXT NOT NULL,                 -- �̸�
    user_level TEXT NOT NULL CHECK (user_level IN ('V', 'S', 'M', 'N')), -- ���ѵ��
    user_level_name TEXT NOT NULL,      -- ���ѵ�޸� (���ΰ�����, ���������, �Ŵ���, �Ϲݴ����)
    branch_code TEXT NOT NULL,          -- �����ڵ� (EA3000, EA3100, EA3200)
    branch_name TEXT NOT NULL,          -- ������ (�߾�����, ��������, ��������)
    phone TEXT NOT NULL,                -- ����ó (010-4444-2445)
    gender TEXT CHECK (gender IN ('M', 'F')), -- ���� (M: ����, F: ����)
    birth_date TEXT,                    -- ������� (YYYY-MM-DD)
    email TEXT,                         -- �̸���
    position TEXT,                      -- ����/��å
    hire_date TEXT DEFAULT (date('now')), -- �Ի���
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')), -- ����
    last_login DATETIME,                -- ������ �α���
    password_changed_date TEXT DEFAULT (date('now')), -- ��й�ȣ ������
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP, -- ������
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP  -- ������
);

-- ���� �ڵ� ���̺�
CREATE TABLE IF NOT EXISTS Branches (
    branch_code TEXT PRIMARY KEY,
    branch_name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    manager_id TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- �⺻ ���� ������ ����
INSERT OR REPLACE INTO Branches (branch_code, branch_name, address, phone) VALUES
('EA3000', '�߾�����', '����� �߱�', '02-1234-5678'),
('EA3100', '��������', '����� ������', '02-2345-6789'),
('EA3200', '��������', '����� ���ʱ�', '02-3456-7890');

-- ���� ����� ������ ���̱׷��̼� (����)
INSERT OR REPLACE INTO Users (user_id, password, name, user_level, user_level_name, branch_code, branch_name, phone, gender, birth_date, position) VALUES
('ct0001', 'ych1123!', '��öȣ', 'V', '���ΰ�����', 'EA3000', '�߾�����', '010-1234-5678', 'M', '1980-01-15', '��ǥ�̻�'),
('ct0002', 'temp_password', '������', 'S', '���������', 'EA3000', '�߾�����', '010-2345-6789', 'F', '1985-03-20', '����'),
('dt0003', 'temp_password', '�迵��', 'M', '�Ŵ���', 'EA3100', '��������', '010-3456-7890', 'F', '1990-07-10', '����'),
('dt0004', 'temp_password', '������', 'N', '�Ϲݴ����', 'EA3100', '��������', '010-4567-8901', 'F', '1992-11-25', '�븮'),
('dt0005', 'temp_password', '���ڱ�', 'N', '�Ϲݴ����', 'EA3200', '��������', '010-5678-9012', 'M', '1988-05-30', '����'),
('dt0006', 'temp_password', '�̿�â', 'M', '�Ŵ���', 'EA3200', '��������', '010-6789-0123', 'M', '1983-09-18', '����'),
('dt0007', 'temp_password', '�����', 'N', '�Ϲݴ����', 'EA3000', '�߾�����', '010-7890-1234', 'M', '1991-12-05', '�븮'),
('ma0001', 'temp_password', '������', 'S', '���������', 'EA3000', '�߾�����', '010-8901-2345', 'M', '1987-04-22', '����');